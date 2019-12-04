#!/usr/bin/env python
# Written by Lilith (thiefyface) <(^.^)> <3
# BSD 3-clause no advert Licensing, etc.
#
# Todo:
# - Expand out regular expressions (e.g. ~["\\] or whatever asn1 had.)

import sys



ignore_list = ["//","grammar","/*"] # for ANTLR specific things we don't care about.
blacklist_list = [".getText()",".matches(","channel(","fragment"]
json_dict = {} # where everything eventually ends up.
important_modifiers = ["?","+","*"]

def main():
    global json_dict
    inp_buf = ""
    out_buf = ""

    try:
        with open(sys.argv[1],"r") as f:
            inp_buf = f.read()                 
    except:
        print "[x.x] Usage: %s <input antlr>"%sys.argv[0]
        sys.exit()

    lines = filter(None,inp_buf.split("\n"))
    new_buf = ""
    for line in lines:
        if line.split(None)[0] in ignore_list:
            continue
    
        for item in blacklist_list:
            for target in line.split(None):
                if item in target:
                    line = line.replace(target,"")    

        if ";" in line:
            line = line[:line.rfind(';')]  + ";\n" # filter out anything after ';'
        if "//" in line:
            line = line[:line.rfind('//')]  + "\n" # 

        new_buf += line + "\n"

    current_item = ""
    ident_list = []
    value_list = []
    
    items = new_buf.split(";")
    for i in range(0,len(items)):
        item_members = items[i].split("\n")

        oneline_item = " ".join(item_members)
        tmp = oneline_item.split(":")
        ident = tmp[0].replace(" ","") 
        value = ":".join(tmp[1:])
             
        
        # Antlr specific transform
        if ident == "moduleDefinition":
            ident = '"<start>"'
        else:
            ident = '"<%s>"'%ident 

        print "%s => %s"%(ident,value)
        json_dict[ident] = []
        ident_list.append(ident)
        value_list.append(value)

    # data should be normalized now such that ident_list[i] corresponds to value_list[i]
    for i in range(0,len(items)):
        ident = ident_list[i]
        value = value_list[i]

        formatted_items = ""
        if "(" in value and ")" in value:
            tmp = paren_to_equiv(value) # top level list
            json_dict[ident] = list_to_good_list(tmp) 
            
            # e.g.: ( asdf ( fdsa, qwer ) ) => [ fdsa_qwer:["fdsa","qwer"], asdf_p_fdsa_qwer_p: [ "asdf", fdsa_qwer ] ] 
                    

            # Begin converting correctly.
            # ----------------------------------------- ANTLR
            # objectSetSpec :                             |  
            #      rootElementSetSpec                     |
            #      | rootElementSetSpec COMMA ELLIPS      V
            # ---------------------------------------- Falk-Grammar
            # => "<objectSetSpec>" : [ ["<rootElementSetSpec>"],["<rootElementSetSpec>","<COMMA>","<ELLIPS>"]] 
            # ---------------------------------------- 
            # first with any parentheses groupings. We replace them with an equivilent item.
            # do not add anything to json_dict yet since we still need to deal with ['?','*','+']
        
            '''
        

            if "|" in inner_value: 
                # add our helper item to the json_dict  
                json_dict[recursion_tag(inner_value)] = inner_value 
                if tmp_value[rparen+1] == "*" or tmp_value[rparen+1] == "+":  
                    resultant_value = 

            else:
                if tmp_value[rparen+1] == "*" or tmp_value[rparen+1] == "+":  
                    # need to add helper item to grammar  
                    json_dict[recursion_tag(inner_value)] = recursion_tag(inner_value) + " | " + inner_value
                    resultant_value = 

                value += inner_value # just strip the parens, they don't matter.
            '''
            
            #json_dict[ident] =   
            


        else: # non recursive items
            pre_parsed = list_to_good_list(value_to_value_list(value)) 
             
            # dumb python always making double quotes into single...
            json_dict[ident] = pre_parsed

       


    outbuf = "{\n"
    for i in json_dict:
        #print "[!.1] %s => %s"%(i, json_dict[i])
        outbuf+= "%s: %s,\n"%(i,json_dict[i]) 

    outbuf = outbuf[:-2] # trim last ','
    outbuf+="\n}"
    with open("%s.json"%sys.argv[1],"w") as f:
        f.write(outbuf) 

    print "[^_^] All done! (output written to %s.json)"%sys.argv[1]


def expand_range(value):
    tmp = filter(None,value.split("'")) 
    try:
        split_int = tmp.index("..")
    except:
        return list(value)

    try:
        lbound = ord(tmp[split_int-1])
        rbound = ord(tmp[split_int+1])+1
        ret_list = [ chr(x) for x in range(lbound,rbound) ] 

    except:
        return list(value)

    return ret_list
                     

def recursion_tag(input_string):
    # Just need a simple conversino for dictionary friendlyness
    out = input_string.replace(" ","_")
    out = out.replace("|","-")
    out = '"<%s_1>"'%out
    return out
    

def value_to_value_list(value_str,joiner=""):
    global json_dict
    return_list = []
    value_items_list = value_str.split("|")
    print "[s_i] : %s"%str(value_items_list)
    #print value_items
    for value_group in value_items_list:
        # create sub-list for all of these.
        item_list = []
        if "'..'" in value_group:
            return_list.append(expand_range(value_group)) 
        else:
            for value in value_group.split(None):
                print "[o_u] : %s" % value
                if value.startswith("<") and value.endswith(">"):
                    tester = '%s'%value
                elif value[-1] in important_modifiers: # *,?,+ 
                    tmp_list = multiplier_to_equiv(value[:-1],value[-1])
                    top_level = 1
                    for item_name,item_val in tmp_list:    
                        if "-2" in item_name: # hacky :/
                            top_level = 2
                        formatted_list = list_to_good_list(item_val)
                        json_dict[item_name] = formatted_list
                    value = "%s-%d"%(value[:-1],top_level)
                    tester = '<%s-%d>'%(value,top_level)
                else:
                    tester = '<%s>'%value
                try:
                    _ = json_dict[tester] 
                    item_list.append("%s"%tester) # cool, it's an id we already know
                    #print "%s found in dict"%tester
                except:
                    if value.startswith("'"):
                        try:
                            item_list.append('%s'%value[1:-1])
                        except Exception as e:
                            print e
                            print "[x.x] Error line? %s"%value
                    elif value.startswith("<") and value.endswith(">"):
                        item_list.append("%s"%value)
                    else:
                        # assuming we hit an item that hasn't been resolved yet...
                        # hopefully it resolves eventually....  \_(^.^)_/
                        item_list.append("<%s>"%value) #

            return_list.append(item_list)

    print "[r_i] : %s" %return_list
    return return_list 


# this function takes a given expression with ['|','+','*','?'] 
# and returns the equivilent set of items in a dict. 
# # e.g. (asdf fdsa)* => only need 1 level of helper items. 
#        { "<asdf_fdsa-1>":[ [], ["<asdf_fdsa">] ] ,  
#          "<asdf_fdsa>": [[ "asdf fdsa"],["<asdf_fdsa-1>"]] }
#
# Note that this function does not handle recursion/nesting. 
# 
# The assumption for this function is that we saw an item like:  
# asdf* or (asdf fdsa)* or (asdf | fdsa)* and the expr is that but without the '*'
#  or asdf+ or asdf?
def multiplier_to_equiv(expr,operator,subst_name=""):
    ret_list = []
    or_expr = expr[:].split("|")
    or_breakout_name = ""

    # this is wrong, it's distributing the modifiers into the inside of the paren.
    or_list = []
    for or_item in or_expr:                 
        normalized_list = []
        normalized = or_item.rstrip().lstrip()
        # e.g. (COMMA boop | doop) => ["COMMA","boop"], ["doop"] 
        and_items = filter(None,normalized.split(" ")) 
        for item in and_items:  
            if item.startswith("'") or item.startswith("<"):
                normalized_list.append(item)
            else:
                normalized_list.append("<%s>"%item)
                 
        or_list.append(normalized_list) 

    
    if subst_name:
        L0_name = subst_name
    elif normalized.startswith("<") and normalized.endswith(">"):
        L0_name = normalized 
    else: 
        L0_name = '<%s>'%normalized.replace(" ","_")

    print ">.> %s | %s"%(L0_name,operator)
    L1_name = '<%s-1>'%L0_name[1:-1]

    if operator == "?":
        L0_value = [ L1_name ] 
        L1_value = [] + or_list  
        ret_list.append(('"%s"'%L0_name,L0_value))
        ret_list.append(('"%s"'%L1_name,L1_value))
        return ret_list

    L0_value = [[L1_name]] + or_list 
    ret_list.append(('"%s"'%L0_name,L0_value))

    L1_value = [ [], [L0_name] ]  
    ret_list.append(('"%s"'%L1_name,L1_value))

    if operator == "+":
        # have to add a third layer so we at least hit once.
        L2_name = '<%s-2>'%L0_name[1:-1] 
        L2_value = or_list + [[L1_name]] 
        ret_list.append(('"%s"'%L2_name,L2_value))

    return ret_list 


#####
def paren_to_equiv(expr):
    global json_dict
    paren_stack = [expr] # Use a stack to deal with nestings.
    top_level_list = []
    top_level_name = ""

    i = 0 
    lbound_ind = 0
    while len(paren_stack) > 0: 
        dup_stoppa = {}
        tmp_value = paren_stack.pop()
        print "%sPopping %s\n"%(" "*len(paren_stack),tmp_value)

        while i < len(tmp_value):
            if tmp_value[i] == "(":
                try:
                    _ = dup_stoppa[tmp_value[i+1:]]
                    # don't care about dups.
                    break
                except:
                    dup_stoppa[tmp_value[i+1:]] = "boop"

                # throw old item back?
                paren_stack.append(tmp_value)
                paren_stack.append(tmp_value[i+1:])
                 
                print "%spushing %s\n"%(" "*len(paren_stack),tmp_value[i+1:])
                tmp_value = tmp_value[i+1:]
                i = 0

            elif tmp_value[i] == ")":

                operator = "" 
                try:
                    if tmp_value[i+1] in important_modifiers:
                        operator = tmp_value[i+1] 
                except:
                    pass
                      
                tmp_value = tmp_value[0:i]
                subst_name = tmp_value.replace(" ","_")
                # if there's a '(' => remove.
                subst_name = subst_name.replace("|","o")
                # quotes kinda f things up too
                subst_name = subst_name.replace("'","")
                subst_name = '<%s>'%subst_name

                try:
                    print "looking for %s"%subst_name
                    _ = json_dict[subst_name] 
                    print "found"
                    # already there,ignore entry
                    break
                except:    
                    print "%s not found, appending"%subst_name
                    pass

                if operator:
                    item_name = ""
                    item_list = ""

                    tmp_list = multiplier_to_equiv(tmp_value,operator,subst_name)
                    for item_name,item_val in tmp_list:    
                        formatted_list = list_to_good_list(item_val)
                        print "[^_^] Inserting into dict: %s => %s"%(item_name, formatted_list)
                        json_dict[item_name] = formatted_list
                else:
                    splitup = value_to_value_list(tmp_value)
                    #print "booper: %s" % str(splitup) 
                    formatted_list = list_to_good_list(splitup) 
                    #print "dooper: %s" % str(formatted_list) 
                    json_dict['"%s"'%subst_name] = formatted_list 
                
                
                # for when we need the top-level list
                top_level_list.append(subst_name)
                top_level_name = subst_name

                print "subst_name: %s, \nformatted_list: %s\n"%(subst_name,formatted_list)
            
                # replace subst_name in next item. 
                try:
                    old_val = paren_stack.pop()
                except:
                    pass

                new_stack = []
                for i in range(0,len(paren_stack)):
                    old_val = paren_stack[i]
                    new_val = old_val.replace("(%s)%s"%(tmp_value,operator),subst_name)
                    new_stack.append(new_val)
                    print "++ %s"%new_val
                    print "\n"

                paren_stack = new_stack[:]
                
                i = 0
                break
            else:
                i+=1

    '''
    if "COMMA_enumerationItem" in top_level_name:
        print repr(top_level_name)
        print repr(top_level_list)
        sys.exit()
    '''

    return top_level_list
    #del(json_dict[top_level_name])

    

# because python is dumb and always does lists with single quotes.
def list_to_good_list(inp_list):
    
    # determine if we need to nest or not
    nest_flag = True
    for item in inp_list: 
        if type(item) == list: 
            nest_flag = False 

    if nest_flag:
        pre_parsed = str([inp_list]) 
    else:
        pre_parsed = str(inp_list) 

    pre_parsed = pre_parsed.replace("'<","\"<")
    pre_parsed = pre_parsed.replace(">'",">\"")
    pre_parsed = pre_parsed.replace("['","[\"")
    pre_parsed = pre_parsed.replace("']","\"]")
    pre_parsed = pre_parsed.replace("',","\",")
    pre_parsed = pre_parsed.replace(", '",", \"")
    pre_parsed = pre_parsed.replace('"""','"\\""')
    pre_parsed = pre_parsed.replace('\'""','"\""')
    
    return pre_parsed


def test_parens(expr):
    global json_dict
    print "*****************************************"
    inp = expr 
    paren_to_equiv(inp)
    print "=-=-------------------------------------"
    print inp
    print "=-=-------------------------------------"
    print json_dict
    ''' 
    for i in json_dict:
        print "%s :"%(i)
        res_buf = ""
        try:
            for j in json_dict[i]:
                res_buf+= "+%s\n" % j 
        except:
            res_buf+= "[x.x] None\n"
        print res_buf 
    '''


if __name__ == "__main__":
    #test_parens("(asdf | ( 'a' | 'b' | 'c' ) | (fdsa | herp derp)? )+")
    #test_parens("(asdf | ( 'f' | ('d' | 'c') ) )")
    main()
    
    



