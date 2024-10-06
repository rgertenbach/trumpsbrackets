# Trumps Brackets

Compare trumps cards (or anything with similar attributes) to see who's the best.

The way this works is as such.

Make a csv that looks like this 

```csv
name,attr1,attr2-,attr3
"Foo",1,2,3.5
"Bar",2,2.2,3.0
"Baz",3,1,1.0
...
```

The name is required.
Cards can have any numbers of arbitrarily named attributes.
If the name of the attribute has a trailihng `-` then the lower the attribute
the better. Otherwise larger is better.

Cards the go through thousands of "tournaments"

-   Cards get paired up randomly.
-   If a card has no opponent it gets seeded to the next round. 
-   Cards get compared, if a card is better in more attributes it wins.
-   If there is a tie a random card progresses.

The program keeps track of how many times each card left the tournament in each
round (or won).


Run the program like this:

```
./trumpsbrackets.py file.csv -n 1000 --no-interactive
```

Arguments:

-   The `file.csv` is the CSV file you created above and is required.
-   `-n`: The number of simulated tournaments to run, defaults to 100,000.
-   `--interactive` / `--no-interactive`: Whether to throw you into an IPython REPL, if you don't pass this it will.


Dependencies:

-   pandas
-   IPython

