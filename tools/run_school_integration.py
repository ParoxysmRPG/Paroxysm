#!/usr/bin/env python3
"""Check the campus routes and uniform shop in a disposable Linux/WSL world."""
from run_dorm_integration import run_test

if __name__ == '__main__':
    run_test('test_school_map.cpp', 'school')
