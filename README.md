# Catalog-App
Catalog App

## Quick Start:

1. This file requires the installation of [psycopg2] (http://initd.org/psycopg/) in order to enter psql command line interface.
2. Clone the repo: ```git clone https://github.com/jowangz/tournament.git```
3. Import the database schema by using command ```psql -f tournament.sql```
4. To test to code: ```python tournament_test.py```
5. ```Success!  All tests pass!``` will be shown if the code ran successfully.

## Expected test case results:

1. Old matches can be deleted.
2. Player records can be deleted.
3. After deleting, countPlayers() returns zero.
4. After registering a player, countPlayers() returns 1.
5. Players can be registered and deleted.
6. Newly registered players appear in the standings with no matches.
7. After a match, players have updated standings.
8. After one match, players with one win are paired.
9. After a draw match, players have updated draw records.

Success!  All tests pass!

## Basic psql commands:

* Use command ```psql tournament``` to enter command line interface.
* Use hot key ```control + D``` to exit command line interface.

## What's included:

```
  movies/
│   ├── tournament.py
│   ├── tournament.sql
│   ├── tournament_test.py
│   ├── README.md
```

## Features:
  
* tournament_test.py includes 9 differenct test case.
* This is a simple swiss pairing python application. It makes matches based on
  the ranking of individual player. This version supports draw game.


## Creator:

**Zheng Wang**

* https://github.com/jowangz

**Udacity**

* https://udacity.com