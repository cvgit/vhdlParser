# vhdlParser

So far the only thing this parser does is take in a file, and generate a tree with all identifiers and Lexer Rules. All information is extracted from VHDL and can be printed to stdout. The only part missing are the functions to group the information.

The reasons to share my project at this early stage are:
- I trust in the cloud for input :)
- I didn't find any free useful SW during my quest
- During my quest I noticed people to be looking for SW to extract port lists, unused signals, dependencies, etc
- I found some people that gave up doing this because 1) starting from scratch is too hard and 2) tools to help might seem overwhelmingly complicated at first
- and ... I'm curious about how this goes.

I should thank the person who wrote a grammar for VHDL, see:
https://github.com/antlr/grammars-v4

I should also tank the person/people developing ANTLR, see:
http://www.antlr.org/

ANTLR uses that grammar to generate a lexer, which translates some input VHDL file into a list of tokens. So you don't need to write 1000s of tricky regexps yourself. It also generates a parser which reads the tokens and a listener that triggers functions like enter_Library_clause(self, ctx), exit_Library_clause(self,ctx) or enter_Identifier(self, ctx) and exit_Identifier(self, ctx). Oh, that's right, I chose to rely on the Python flavor of ANTLR.

Besides trying to get ANTLR running and understand the basics, I wrote a generic class that overrides these enter_ and exit_ methods to generate a tree data structure along with a print function. The leafs of the trees are the Identifiers, the text of which is obviously also stored. Language keywords are not stored to date, though that would merely take minutes to add if necessary.

Example output:
reading file ../vhdlparser/spaceinvaders.vhd
file
|   Design_file
|   |   Design_unit
|   |   |   Context_clause
|   |   |   |   Context_item
|   |   |   |   |   Library_clause
|   |   |   |   |   |   Logical_name_list
|   |   |   |   |   |   |   Logical_name
|   |   |   |   |   |   |   |   ieee(Identifier)
...
