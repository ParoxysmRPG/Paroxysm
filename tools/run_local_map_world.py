#!/usr/bin/env python3
"""Boot only a disposable world to verify map commands and loaded helpfiles."""
from run_dorm_integration import run_test

if __name__ == '__main__':
    run_test('test_local_map_world.cpp', 'local-map-world')
