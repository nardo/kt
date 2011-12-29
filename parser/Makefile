LEX=flex
YACC=bison
CPPFLAGS=-I/usr/include/python2.5 -I../../ -I../standard_library
LDFLAGS=-lpython2.5 -lstdc++ -framework Foundation
python: main.o parser.o lexical_analyzer.o
	$(CC) -o $@ $(LDFLAGS) $^

main.o: main.M parser_interface.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c main.M

parser.o: parser.cpp parser_interface.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c parser.cpp

parser.cpp: parser.bison
	$(YACC) parser.bison

lexical_analyzer.o: lexical_analyzer.cpp
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c lexical_analyzer.cpp

lexical_analyzer.cpp: lexical_analyzer.flex
	$(LEX) $(LFLAGS) -o $@ lexical_analyzer.flex

clean:
	rm python *.o lexical_analyzer.cpp parser.cpp parser.hpp parser.output
