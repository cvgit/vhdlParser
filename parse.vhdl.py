from __future__ import print_function
import sys
import os
import re

#extend path to find antlr4
sys.path.append("{}/vhdl".format(os.getcwd()))
import antlr4
from antlr4 import *
from antlr4 import tree
from vhdlLexer import vhdlLexer
from vhdlParser import vhdlParser
from vhdlListener import vhdlListener
from vhdlVisitor import vhdlVisitor
from antlr4.tree.Trees import Trees

from collections import defaultdict


#Data structure
class TreeStorage():
    """Tree data structure with parents and children
    """
    #keep track of instantiations
    Trees = []
    
    #internals
    ##tell __init__ a child is made, dont add to list above
    _child = False
    
    #add new root instance to list Trees above
    #initiate some variables
    def __init__(self,*args):
        name = args[0]
        if not TreeStorage._child:
            TreeStorage.Trees.append(self)
            self.type = "file"
            self.name = args[0]
        else:
            self.type = args[0]
        #parental links    
        self.children = []
        self.parent = None
        #empty dictionary
        self.data = {}
        #empty string
        self.text = ""
        #counter used for a.o. printing of tree
        self._purge = False
        self._depth = 0
    
    def delete(self):
        if self._depth == 0:
            Trees.remove(self)
        else:
            self.parent.children.remove(self)
        del self
    
    #add a child/branch to a node or tree
    #define parental relationship
    def makeChild(self, type):
        TreeStorage._child = True
        child = TreeStorage(type)
        TreeStorage._child = False
        child.parent = self
        child._depth = self._depth + 1
        self.children.append(child)
        return child
    
    #fill in text attribute of member
    def addText(self, text):
        self.text = text
    
    #add data to dictionary "data"
    def addToDataList(self, item, property):
        if item in self.data.keys():
            self.data[item].append(property)
        else:
            self.data[item] = [property]
    
    #return name of object
    def getName(self):
        return self.name
    
    #get parent of object
    def getParent(self):
        return self.parent
     
    #get children of object
    def getChildren(self):
        return self.children
        
    def getFirstChildofType(self,type):
        return [x for x in self.children if x.type == type][0]
    
    #get siblings of object, including object, also for roots
    def getSiblings(self):
        if self._depth == 0:
            return [tree for tree in TreeStorage.getTrees() if tree is not self]
        else:
            return [sibling for sibling in self.parent.children if self is not sibling]
 
    def getFirstSiblingofType(self,type):
        return [x for x in self.getSiblings() if x.type == type][0]
        
    #check if object has children
    def hasChildren(self):
        return not not self.children
        
    #quick and dirty print of a tree originating from any object
    def printSubTree(self):
        text = "|   "*self._depth
        text = text + self.text
        if not self.type == "":
            text = text + " ("+self.type+")"
        print(text)
        if not self.data == {}:
            for entry in self.data.keys():
                print("|   "*self._depth + "  -> " + entry + ":" + str(self.data[entry]))
        
        if self.hasChildren():
            for child in self.children:
                child.printSubTree()     
                
    def printTree():
        for tree in TreeStorage.Trees:
            print("Root: {}".format(tree.name))
            tree.printSubTree()
    
    def getTree(name):
        return roots(name)
        
    def getTrees():
        return TreeStorage.Trees
        
    #return first ancestor of certain type, if any.
    def getAncestor(self,type):
        if self.parent is None:
            return False
        elif self.parent.type == type:
            return self.parent
        else:
            return self.parent.getAncestor(type)
                
    def hasAncestor(self,type):
        result = self.getAncestor(type)
        if result is False:
            return False
        else:
            return True
            
    def setPurge(self):
        self._purge = True

    #get all children, grandchildren etc of node
    _level = 0              
    _list = []
    def getAllChildren(self):
        TreeStorage._level = TreeStorage._level + 1
        for child in self.children:
            TreeStorage._list.append(child)
            child.getAllChildren()
        TreeStorage._level = TreeStorage._level - 1
        if TreeStorage._level == 0:
            childrenlist = TreeStorage._list
            TreeStorage._list = []
            return childrenlist
    
    #get all children, grandchildren of node with particular type
    def getAllChildrenOfType(self,type):
        return [x for x in self.getAllChildren() if x.type == type]
            
    def mergeSelectedName(self):
        for x in self.getAllChildrenOfType("Selected_name"):
            name = ""
            for y in x.getAllChildrenOfType("Identifier"):
                if not name == "":
                    name = name + "."
                name = name + y.text
                y.setPurge()
            x.text = name
        self.purge()
        
    def extractlib(self):
        for x in [x for x in self.getAllChildrenOfType("Identifier") if x.hasAncestor("Library_clause")]:
            x.getAncestor("Design_unit").data.setdefault("libs",[]).append(x.text)
            x.setPurge()
        self.purge()
        
    #run mergeSelectedName first
    def extractuse(self):
        for x in [x for x in self.getAllChildrenOfType("Selected_name") if x.hasAncestor("Use_clause")]:
            x.getAncestor("Design_unit").data.setdefault("use",[]).append(x.text)
            x.setPurge()    
        self.purge()
        
    #run mergeSelectedName first
    def extractgenerics(self):
        for x in [x for x in self.getAllChildrenOfType("Identifier") if x.hasAncestor("Generic_clause")]:
            if x.parent.type == "Identifier_list":
                generic = x
                type = x.parent.getFirstSiblingofType("Subtype_indication").getFirstChildofType("Selected_name")
                x.getAncestor("Design_unit").data.setdefault("generic",[]).append({generic.text:type.text})
                x.setPurge()
                type.setPurge()
            elif x.parent.type == "Enumeration_literal":
                x.getAncestor("Design_unit").data.setdefault("extconstants",[]).append({x.text:"generic_constant"})
                x.setPurge()
        self.purge()
        
    #run mergeSelectedName first
    def extractentityport(self):
        for x in [x for x in self.getAllChildrenOfType("Identifier") if x.hasAncestor("Port_clause") and x.hasAncestor("Entity_header")]:
            if x.parent.type == "Identifier_list":
                signal = x
                type = x.parent.getFirstSiblingofType("Subtype_indication").getFirstChildofType("Selected_name")
                x.getAncestor("Design_unit").data.setdefault("entityport",[]).append({signal.text:type.text})
                x.setPurge()
                type.setPurge()
        self.purge()
            
    #remove branches marked to purge
    def purge(self):
        #first kill the children
        for x in self.getAllChildren():
            if x._purge:
                x.delete()
        
    def clean(self):
        if self.text == "" and self.data == {} and self.children == []:
            self.delete()
            return True        
        repeat = False
        for x in self.children:
            res = x.clean()
            repeat = repeat or res      
        if repeat:
            self.clean()
        return repeat


        

            


#function to generate overruling class
def generate_stubbed_class(klass_name, klass):
    """Returns a function call to create a class derrived from "klass",
    named "klass_name" which autogenerates a bunch of override methods 
    for "klass" attributes.
    Specifically, this function will return a class which overrides all
    enterXXXX() and exitXXXX() methods from the Listener class generated
    by ANTLR so to set an attribute XXXX True upon entering and False 
    upon exit.
    """
    #override enter_NAME to add a branch and cling to it
    def generate_stub_enter(name):
        def stub(self, ctx):
            self.makeBranchAndClimb(name)
        return stub #return method
        
    #override exit_NAME to back down one branch   
    def generate_stub_exit(name):
        def stub(self, ctx):
            self.climbBack()
        return stub #return method
        
    #empty list of attributes
    attributes = {}
    
    for name in dir(klass): # lists all attributes (names only)
        try:
            #match uppercase, but don't absorb it
            #split enterIdentifier in [], "enter", "Identifier", []
            oper, key = re.split('(^enter|^exit)(.*)',name,1)[1:3]
        except ValueError:
            # not in the format of SOMETHING_SOMETHING
            continue #try next
            
        #skip inherited rule which is called every time
        if key == 'EveryRule':
            continue
            
        #additional check    
        attr = getattr(klass, name)        
        # make sure it's a function and name ends in _enter or _exit
        if callable(attr) and oper in ('enter', 'exit'):
            #call method generation function
            if oper == 'enter': # True for 'enter', False for 'exit'
                attributes[name] = generate_stub_enter(key)
            else:
                attributes[name] = generate_stub_exit(key)
    #return a class, inheriting from klass, with generated attributes
    return type(klass_name, (klass,), attributes)

#L istener class    
class L(generate_stubbed_class('MyClass', vhdlListener)):
    """Class which overrides methods defined in myclass, which 
    were automatically derrived from vhdlListener
    """  
    def __init__(self, filename):
        #instantiate a tree storage structure
        self.root = TreeStorage(filename,"file")
        #set pointer
        self.tree = self.root
        
    def makeBranchAndClimb(self, type):
        self.tree = self.tree.makeChild(type)
            
    def climbBack(self):
        self.tree = self.tree.parent
    
    def printTree(self):
        self.root.printDetailedSubTree()
        
    #overrule one more time to store its text
    #basically this is all we want
    def enterIdentifier(self,ctx):
        super(L,self).enterIdentifier(ctx)
        self.tree.addText(ctx.getText())
      
        
def main(argv):
    filename = argv[1]
    print("reading file {}".format(filename))
    
    #take input
    input = FileStream(filename)
    
    #translate vhdl source into tokens
    lexer = vhdlLexer(input)
    
    #list of tokens
    stream = CommonTokenStream(lexer)
    
    #looking up vhdl.g4
    #and match token stream to grammar
    parser = vhdlParser(stream)
    
    #start tree at main entrance
    tree = parser.design_file()
    walker = ParseTreeWalker()
    
    #create member of class L
    listener = L(filename)
    
    #walk the listener through the tree
    walker.walk(listener, tree)
    
    #take tree representation of code
    tree = listener.tree
    
    tree.mergeSelectedName() #important to be first
    tree.extractlib()
    tree.extractuse()
    tree.extractgenerics()
    tree.extractentityport()
    tree.clean()
    
    
    #print that tree
    tree.printSubTree()
    
if __name__ == '__main__':
    main(sys.argv)
