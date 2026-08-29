"""
Smart Rail Algorithms Package.

Hosts individual pathfinding and scheduling deconfliction algorithms:
BFS, DFS, Dijkstra, Floyd-Warshall, Greedy, CSP/CNF, Priority EDF, and Dynamic Reroute.
"""

from algorithms.base import BaseScheduler, ReservationTable
from algorithms.bfs import bfs_path
from algorithms.dfs import dfs_path
from algorithms.dijkstra import dijkstra_path
from algorithms.floyd_warshall import floyd_warshall_all_pairs
from algorithms.greedy import GreedyScheduler
from algorithms.cnf_csp import CSPScheduler
from algorithms.priority_edf import PriorityEDFScheduler
from algorithms.dynamic_reroute import DynamicRerouteScheduler

ALGORITHM_REGISTRY = {
    "CSP": CSPScheduler,
    "GREEDY": GreedyScheduler,
    "PRIORITY_EDF": PriorityEDFScheduler,
    "DYNAMIC_REROUTE": DynamicRerouteScheduler,
}

PATHFINDING_REGISTRY = {
    "DIJKSTRA": dijkstra_path,
    "BFS": bfs_path,
    "DFS": dfs_path,
}
