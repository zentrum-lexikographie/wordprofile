VERSION = 3.02
CC = /usr/bin/g++
CFLAGS  = -static -O5 -Wno-deprecated -std=c++11
LDFLAGS = -lexpat
INCLUDE = ./source/include/
BINARY = ./bin/
SRC = ./source/src/


all: $(BINARY)mapping $(BINARY)preprocessing $(BINARY)postprocessing $(BINARY)statistics $(BINARY)clean_and_sort $(BINARY)score_examples $(BINARY)concordances $(INCLUDE)LexerRules.h

$(INCLUDE)LexerRules.h: ./spec/LexerRules.re2c
	re2c -o $@ ./spec/LexerRules.re2c

$(BINARY)%: $(SRC)%.o
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(SRC)%.o: $(SRC)%.cpp $(INCLUDE)read_specification.h $(INCLUDE)hashes.h $(INCLUDE)LexerRules.h $(INCLUDE)read_doubles.h
	$(CC) $(CFLAGS) -o $@ -I $(INCLUDE) -c $<


.PHONY: clean

clean:
	rm -rf $(BINARY)* $(SRC)*.o $(INCLUDE)LexerRules.h


