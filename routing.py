from util import find_loops, print_exceeded
from classes import DngResult, NgResult
import time

"""
This function calculates the optimal path and cost for a routing problem using a 
modified dynamic programming approach that takes into account a given upper bound on cost.
"""
def ng_routing(starting_node, nodes, costs_list, upper_bound):
    start = time.time()

    # Counters for various extension cases
    ub_ext = 0
    lut_ext = 0
    all_ext = 0
    lut_up_ext = 0
    followed_ext = 0
    oob_ext = 0

    # Function to retrace the optimal path from the dynamic programming table
    def retrace_optimal_path(buffer):
        # Filter out only the full paths
        full_path_buffer = dict((k, v) for k, v in buffer.items() if k[2] == n)

        # Select the path with the lowest cost
        path_key = min(full_path_buffer.keys(), key=lambda x: full_path_buffer[x][0])
        curr_node = path_key[0]
        optimal_cost, prev_node, ng_set_i = buffer[path_key]

        # Retrace the optimal path using the stored previous nodes
        optimal_path = [curr_node, starting_node]
        k = n
        while prev_node is not None:
            curr_node = prev_node
            k -= 1
            path_key = (curr_node, ng_set_i, k)
            _, prev_node, ng_set_i = buffer[path_key]
            optimal_path = [curr_node] + optimal_path

        return optimal_path, optimal_cost

    all_dp_routes = {}
    node_objects = {node.number: node for node in nodes}
    n = len(node_objects)
    all_nodes = frozenset(list(node_objects.keys()))
    all_nodes = frozenset(all_nodes) - frozenset([starting_node])
    ng_set_i = frozenset()
    k = 1
    state = (starting_node, ng_set_i, k)
    all_dp_routes[state] = (0, None, frozenset())
    queue = [state]

    # Main loop for dynamic programming
    while queue:
        current_node, ng_set_i, k = queue.pop(0)
        prev_cost, _, _ = all_dp_routes[(current_node, ng_set_i, k)]

        # Get the neighbours of the current node
        neighbours = frozenset(nodes[current_node].neighbors)

        # Update the set of visited nodes (ng_set_j) based on the current node and its neighbours
        ng_set_j = frozenset.intersection(ng_set_i, neighbours)
        ng_set_j = frozenset().union(ng_set_j, frozenset([current_node]))
        k += 1

        # Check if we have visited all nodes
        if k > n:
            oob_ext += 1
            continue

        # Determine the nodes yet to be visited
        to_visit = all_nodes - ng_set_j
        for new_curr_node in to_visit:
            all_ext += 1

            # Calculate the new cost of the path
            new_cost = round((prev_cost + ((n - k + 2) * costs_list[current_node][new_curr_node])), 3)

            # Check if the new cost exceeds the upper bound
            if new_cost > upper_bound:
                ub_ext += 1
                continue
            # If the current state is not in the dynamic programming table, add it
            elif (new_curr_node, ng_set_j, k) not in all_dp_routes:
                followed_ext += 1
                all_dp_routes[(new_curr_node, ng_set_j, k)] = (new_cost, current_node, ng_set_i)
                queue += [(new_curr_node, ng_set_j, k)]
            # If the new cost is lower than the existing cost in the table, update it
            elif new_cost < all_dp_routes[(new_curr_node, ng_set_j, k)][0]:
                lut_up_ext += 1
                all_dp_routes[(new_curr_node, ng_set_j, k)] = (new_cost, current_node, ng_set_i)
            # If the new cost is not better, skip the current iteration
            else:
                lut_ext += 1

    # Get the full path buffer from the dynamic programming table
    full_path_buffer = dict((k, v) for k, v in all_dp_routes.items() if k[2] == n)

    # Calculate the final cost, including the cost from the last node to the starting node
    for key in full_path_buffer.keys():
        cost, prev_node, ng_set_i = all_dp_routes[key]
        new_cost = round(cost + costs_list[key[0]][starting_node], 3)
        all_dp_routes[key] = (new_cost, prev_node, ng_set_i)

    # Retrieve the optimal path and cost
    optimal_path, optimal_cost = retrace_optimal_path(all_dp_routes)

    # Check if the path is elementary (has no loops)
    elementary = False
    if len(find_loops(optimal_path)) == 0:
        elementary = True

    end = time.time()
    return NgResult(optimal_path, round(optimal_cost, 3), elementary, len(node_objects[0].neighbors),
                    round(end - start, 3), all_ext, followed_ext, ub_ext, lut_ext, lut_up_ext, oob_ext, len(full_path_buffer))


# Implementation of the Dynamic Ng-Path Relaxation
def dynamic_ng_pathing(starting_node, nodeObjects, costs_list, delta2, upper_bound):
    start = time.time()
    i = 0

    results = []
    start_delta1 = len(nodeObjects[0].neighbors)
    max_delta1 = 0

    while True:
        i += 1

        # Calculate the optimal route using the ng_routing function
        result = ng_routing(starting_node, nodeObjects, costs_list, upper_bound)
        loops = find_loops(result.best_route)

        # Update the maximum number of neighbors
        for node in nodeObjects:
            if len(node.neighbors) > max_delta1:
                max_delta1 = len(node.neighbors)

        # If the optimal route is loop-free, return the result
        if len(loops) == 0:
            print("")
            print("Best Route in iteration: " + str(i))
            print(result.best_route)
            print("Costs :", str(result.cost))
            end = time.time()
            result = DngResult(result.best_route, result.cost, len(loops), start_delta1, max_delta1, delta2, False,
                               True, i, round(end - start, 3), result.all_ext, result.followed_ext, result.ub_ext,
                               result.lut_ext, result.lut_up_ext, result.oob_ext, result.feasible_solutions)
            results.append(result)
            return result, results

        print("")
        print(str(i) + ". Iteration")
        print(result.best_route)
        print("Costs :", str(result.cost))
        print("Sub Routes:")
        print(loops)
        end = time.time()

        # If the optimal route has loops, try to remove them by adding neighbors
        loop_with_smallest_cardinality = min(loops, key=len)
        start_and_ending_node = loop_with_smallest_cardinality[0]
        loop_with_smallest_cardinality = loop_with_smallest_cardinality[1:-1]

        # If the loop has more nodes than delta2, return the result as exceeded
        if len(loop_with_smallest_cardinality) >= delta2:
            print_exceeded(result.best_route, result.cost)
            end = time.time()
            result = DngResult(result.best_route, result.cost, len(loops), start_delta1, max_delta1, delta2, True,
                               False, i, round(end - start, 3), result.all_ext, result.followed_ext, result.ub_ext,
                               result.lut_ext, result.lut_up_ext, result.oob_ext, result.feasible_solutions)
            return result, results

        # Add neighbors to remove loops from the optimal route
        for node in nodeObjects:
            for route_node in loop_with_smallest_cardinality:
                if node.number == route_node and start_and_ending_node not in node.neighbors:
                    if len(node.neighbors) < delta2:
                        node.neighbors.append(start_and_ending_node)
                    else:
                        print_exceeded(result.best_route, result.cost)
                        end = time.time()
                        result = DngResult(result.best_route, result.cost, len(loops), start_delta1, max_delta1, delta2,
                                           True, False, i, round(end - start, 3), result.all_ext, result.followed_ext,
                                           result.ub_ext,
                                           result.lut_ext, result.lut_up_ext, result.oob_ext, result.feasible_solutions)
                        return result, results

        result = DngResult(result.best_route, result.cost, len(loops), start_delta1, max_delta1, delta2, False,
                           False, i, round(end - start, 3), result.all_ext, result.followed_ext, result.ub_ext,
                           result.lut_ext, result.lut_up_ext, result.oob_ext, result.feasible_solutions)
        results.append(result)


# A  Version of the Ng-Route Algorithm without usage of enhancement measures
def ng_routing_depr(starting_node, node_objects, costsList):
    start = time.time()
    all_ext = 0

    all_feasible_ng_routes = {}
    node_objects = {node.number: node for node in node_objects}
    all_nodes = list(node_objects.keys())
    all_nodes.remove(starting_node)
    ng_set_i = frozenset()
    n = len(node_objects)
    stack = [(starting_node, ng_set_i, [], 0.0)]

    while stack:
        all_ext += 1
        node, ng_set_i, visited, costs = stack.pop()
        node_object = node_objects[node]

        neighbours = frozenset(node_object.neighbors)
        ng_set_j = frozenset.intersection(ng_set_i, neighbours)
        ng_set_j = frozenset().union(ng_set_j, frozenset([node]))

        visited.append(node)
        to_visit = [node for node in all_nodes if node not in ng_set_j]

        if len(visited) == n:
            new_cost = costs + costsList[visited[len(visited) - 1]][starting_node]
            visited.append(starting_node)
            all_feasible_ng_routes[new_cost] = visited
            continue

        for node in to_visit:
            new_cost = costs + (n - len(visited)) + 1 * costsList[visited[len(visited) - 1]][node]
            stack += [(node, ng_set_j, visited.copy(), new_cost)]

    else:
        cost = min(all_feasible_ng_routes.keys())
        best_route = all_feasible_ng_routes[cost]
        loops = find_loops(best_route)

        elementary = False
        if len(loops) == 0:
            elementary = True

        end = time.time()
        return NgResult(best_route, cost, elementary, len(node_objects[0].neighbors), round(end - start, 3), all_ext, 0, 0, 0, 0, 0, len(all_feasible_ng_routes))
