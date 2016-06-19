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


class UniqueList(list):
    """Class derrived from list. It overrides the append method 
    only to append an object to its member if it is unique to that member    
    """
    def append(self, item):
        if not item in self:
            #from UniqueList's parent (=list), take "self"
            super(UniqueList,self).append(item)

class TreeStorage(UniqueList):
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
        self.parent = []
        #empty dictionary/list
        self.data = {}
        self.text = ""
        #counter used for a.o. printing of tree
        self._depth = 0
    
    
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
    
    #get siblings of object, including object, also for roots
    def getSiblings(self):
        if self.depth == 0:
            return [tree for tree in TreeStorage.getTrees() if tree is not self]
        else:
            return [sibling for sibling in self.parent.children if self is not sibling]
    
    #check if object has children
    def hasChildren(self):
        return not not self.children
        
    #quick and dirty print of a tree originating from any object
    def printSubTree(self):
        if self.text == "":
            print("|   "*self._depth + self.type)
        else:
            print("|   "*self._depth + self.text + "(" + self.type +")")
        if self.hasChildren():
            for child in self.children:
                child.printSubTree()    
    
    #same with more info
    def printDetailedSubTree(self):
        print("|   "*self.depth + "{}: {}".format(self.type,self.text))
        if self.hasChildren():
            for child in self.children:
                child.printDetailedSubTree()   
                
    def printTree():
        for tree in TreeStorage.Trees:
            print("Root: {}".format(tree.name))
            tree.printSubTree()
    
    def getTree(name):
        return roots(name)
        
    def getTrees():
        return TreeStorage.Trees
        
    #return first ancestor of certain type, if any.
    def hasAncestor(self,type):
        try:
            if self.parent.name == type:
                return self.parent
            else:
                self.parent.hasAncestor(type)
        except:
            return False
        
        
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
    
    #get all children, grandchilrren of node with particular type
    def getAllChildrenOfType(self,type):
        return [x for x in self.getAllChildren() if x.type == type]
        
            
    def extractlib(self):
        print(self.getAllChildrenOfType("Identifier"))
        print ([x.text for x in self.getAllChildrenOfType("Identifier") if x.hasAncestor("library_clause")]) 
        

    
def generate_stubbed_class(klass_name, klass):
    """Returns a function call to create a class derrived from "klass",
    named "klass_name" which autogenerates a bunch of override methods 
    for "klass" attributes.
    Specifically, this function will return a class which overrides all
    enterXXXX() and exitXXXX() methods from the Listener class generated
    by ANTLR so to set an attribute XXXX True upon entering and False 
    upon exit.
    """
    def generate_stub_enter(name):
        def stub(self, ctx):
            # toggle variable with name of rule
            self.makeBranchAndClimb(name)
        return stub
        
    def generate_stub_exit(name):
        def stub(self, ctx):
            # toggle variable with name of rule
            self.climbBack()
        return stub
    
    attributes = {}
    
    for name in dir(klass): # lists all attributes (names only)
        try:
            #match uppercase, but don't absorb it
            oper, key = re.split('(^enter|^exit)(.*)',name,1)[1:3]
        except ValueError:
            # not in the format of SOMETHING_SOMETHING
            continue
        attr = getattr(klass, name)
        
        #skip inherited rule
        if key == 'EveryRule':
            continue
        
        # make sure it's a function and name ends in _enter or _exit
        if callable(attr) and oper in ('enter', 'exit'):
            if oper == 'enter': # True for 'enter', False for 'exit'
                attributes[name] = generate_stub_enter(key)
            else:
                attributes[name] = generate_stub_exit(key)
    
    return type(klass_name, (klass,), attributes)



    
class L(generate_stubbed_class('MyClass', vhdlListener)):
    """Class which overrides methods defined in myclass, which 
    were automatically derrived from vhdlListener
    """  
    def __init__(self, filename):
        self.root = TreeStorage(filename,"file")
        self.tree = self.root
        
    def makeBranchAndClimb(self, type):
        self.tree = self.tree.makeChild(type)
            
    def climbBack(self):
        self.tree = self.tree.parent
    
    def printTree(self):
        self.root.printDetailedSubTree()
        
    #overrule one more time to store it's text
    def enterIdentifier(self,ctx):
        super(L,self).enterIdentifier(ctx)
        self.tree.addText(ctx.getText())
        
class vhdlProcessTree(TreeStorage):
    list = []
    level = 0
      
        
def main(argv):
    filename = argv[1]
    print("reading file {}".format(filename))
    input = FileStream(filename)
    lexer = vhdlLexer(input)
    while True:
        token = lexer.nextToken()
        #print(token)
        #print("tokenID {} = {}".format(token.type,vhdlLexer.symbolicNames[token.type]))
        if token.type == vhdlParser.EOF:
            break
    # go back to first token
    lexer.reset()
    
    #list of tokens
    stream = CommonTokenStream(lexer)
    
    parser = vhdlParser(stream)
    #looking up vhdl.g4
    tree = parser.design_file()
    walker = ParseTreeWalker()
    
    #create member of class L, performing actions on enterSmth, exitSmth
    #defined in vhdlListener
    listener = L(filename)
    
    #walk the listener through the tree
    walker.walk(listener, tree)
    
    tree = listener.tree
    tree.printSubTree()
    tree.extractlib()
    
    
    
if __name__ == '__main__':
    main(sys.argv)
