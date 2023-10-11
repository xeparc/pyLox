"""Interpreter interface"""
from .scan import tokenize

def repl():
    """Read, evaluate, print loop. Infinite loop that interprets user inputs,
    evaluates them and prints the result on screen."""
    
    while True:
        line = input('jlox > ')
        print(evaluate(line))


def run(content):
    for line in content.split('\n'):
        evaluate(line)

def evaluate(line):
    tokens = tokenize(line)
    return " ".join((str(t) for t in tokens))
