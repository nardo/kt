LEX=flex
YACC=bison
CPPFLAGS=-I/usr/include/python2.5
LDFLAGS=-lpython2.5 -lstdc++
parser: main.o parser.o lexical_analyzer.o
	$(CC) -o $@ $(LDFLAGS) $^

main.o:
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c main.cpp

parser.o: parser.cpp
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c parser.cpp

parser.cpp: parser.bison
	$(YACC) parser.bison

lexical_analyzer.o: lexical_analyzer.cpp
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c lexical_analyzer.cpp

lexical_analyzer.cpp: lexical_analyzer.flex
	$(LEX) $(LFLAGS) -o $@ lexical_analyzer.flex

clean:
	rm parser *.o lexical_analyzer.cpp parser.cpp parser.hpp parser.output
