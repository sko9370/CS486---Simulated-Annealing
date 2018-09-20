'''
Created on Aug 30, 2012
Modified for AI class on 9 Sep 2018

@author: alexander.mentis

Solve QAP using simulated annealing.
'''

'''
https://sebastianraschka.com/Articles/2014_multiprocessing.html#introduction-to-the-multiprocessing-module
I read how to use multiprocessing and used the code from the library to define a queue and
make a list of processes. I ended up not using it though... It was taking too long
and I had other stuff to study.
'''

import multiprocessing as mp

import copy
import math
import random

def init_flow(infile):
    """
    Initialize and return the flow matrix.

    Reads the file pointed to by infile. The file must have the following
    format:

    Line x should contain the list of flow values from department x+1 to
    departments 1 through x-1, each flow separated by whitespace. A blank line
    terminates the file, so file comments can be inserted after one or more
    blank lines.
    """

    flows = []
    for line in infile:
        if line.strip():
            flows.append([int(flow) for flow in line.split()])
        else:
            break

    return flows

def init_locations(flows):
    """
    Set initial department locations randomly.
    """
    num_departments = len(flows) + 1 # flows doesn't have row for 1st department

    # assume rectangular layouts
    rows = math.floor(math.sqrt(num_departments))
    cols = math.ceil(num_departments / rows)

    dept_iter = iter(random.sample(range(num_departments), num_departments))

    return [[next(dept_iter) for col in range(cols)] for row in range(rows)]

def cost(locations, flows):
    """
    Calculates the cost based on the rectilinear distance between the source
    and destination times the flow.
    """

    total_cost = 0

    # flow is symmetrical, so to avoid double-counting flow, we only count flow
    # from locations below each current location and exit the loop as soon as
    # it reaches the current location
    for r1, r1_depts in enumerate(locations):
        for c1, dept1 in enumerate(r1_depts):
            try:
                for r2, r2_depts in enumerate(locations):
                    for c2, dept2 in enumerate(r2_depts):
                        if r2 == r1 and c2 == c1:
                            # break out of two inner loops
                            raise StopIteration
                        else:
                            # the flows lookup table is a half-matrix, so
                            # we have to make sure we use the largest department
                            # for the row and the smallest for the column
                            lo, hi = ((dept1, dept2) if dept1 < dept2
                                                            else (dept2, dept1))
                            dist = abs(r2-r1) + abs(c2-c1)

                            # the half-matrix has no row for the first
                            # department, so we subtract 1 from the dept number
                            # to get the correct row; we never have to worry
                            # about 0 being the hi_dept, since another
                            # department will always be higher and force 0 to
                            # the the lo_dept
                            total_cost += flows[hi-1][lo] * dist
            except StopIteration:
                continue

    return total_cost

def swap(locations, r1, c1, r2, c2):
    """
    Swaps the departments at the specified x, y coordinates in the locations
    grid.
    """

    locations[r1][c1], locations[r2][c2] = locations[r2][c2], locations[r1][c1]

def move(locations):
    """
    Perturb the department arrangement by swapping two department locations.
    Returns a tuple containing the locations swapped for use with undo swap, if
    necessary.
    """

    r1 = random.choice(range(len(locations)))
    c1 = random.choice(range(len(locations[r1])))

    r2 = random.choice(range(len(locations)))
    c2 = random.choice(range(len(locations[r2])))

    while r1 == r2 and c1 == c2:
        r2 = random.choice(range(len(locations)))
        c2 = random.choice(range(len(locations[r2])))

    swap(locations, r1, c1, r2, c2)

    return (r1, c1, r2, c2)

def init_temperature(locations, flows, init_accept_rate):
    """
    Calculate the initial annealing temperature.

    Following Dreo, et al. (2006), calculate the average energy change over 100
    random moves. Derive init_temp from exp(-avg_change/init_temp) = tau_0,
    where tau_0 is provided by the user. A tau_0 value of 0.50 represents an
    assumed poor initial configuration, whereas a tau_0 value of 0.20 represents
    an assumed good one.
    """

    delta_E = []
    for trial in range(100):
        start_cost = cost(locations, flows)
        move(locations)
        end_cost = cost(locations, flows)
        delta_E.append(abs(end_cost - start_cost))

        avg_delta_E = sum(delta_E) / len(delta_E)

    return -(avg_delta_E) / math.log(init_accept_rate)

def main():
    """
    Program entry point. Parses command line arguments and contains the main
    simulated annealing loop.
    """

    # Read flow data and generate initial department locations
    with open("input.txt") as infile:
        flows = init_flow(infile)

    num_departments = len(flows) + 1
    locations = init_locations(flows)

    # Implement SA algorithm here

    tau = input("Choose a value from 0.2 (good initial config) to 0.5 (bad initial config): ")
    if tau == "":
        tau = 0.5

    #tau = 0.5
    temperature = init_temperature(locations, flows, float(tau))

    N = input("Change N (number of parameters) if you'd like: ")
    if N == "":
        N = 15
    else:
        N = int(N)
    print("calculating...")

    #N = 15

    failed_temps = 0
    stage_fail = 0
    accepted = 0
    attempted = 0
    least = 1000

    while stage_fail < 3:
        current_cost = cost(locations, flows)
        r1, c1, r2, c2 = move(locations)
        new_cost = cost(locations, flows)

        if new_cost < current_cost:
            accepted += 1
            '''
            Seo, Steve H-4 '19. 2018 Sep 19. Assistance given to the author, verbal discussion.
            CDT Seo told me that he thought that this if statement should also
            increment attempted counts instead of just accepted counts as I had
            before. Although the effect is minimal and possibly not always positive,
            I think this is how you should count accepts and attempts. West Point, NY.
            '''
            attempted += 1
            least = new_cost

        else:
            # Acceptance rule of Metropolis
            change_E = new_cost - current_cost
            accept = math.exp( -(change_E) / temperature )
            # R random from [0,1]
            r = random.random()
            # if good temperature, continue
            if r < accept:
                attempted += 1
            else:
                attempted += 1
                swap(locations, r2, c2, r1, c1)

        # decrease temperature; can use 0.9 old_temp = new_temp
        if attempted == 100*N or accepted == 12*N:
            temperature = 0.9 * temperature
            # check if failed this round
            if accepted == 0:
                stage_fail += 1
            # reset stage_fail if not consecutive fails
            else:
                stage_fail = 0
            # reset values
            attempted = 0
            accepted = 0

    print(least)
    return least

if __name__ == '__main__':
    '''
    output = mp.Queue()
    processes = [mp.Process(target = main(), args = ()) for x in range(3)]

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    results = [output.get() for p in processes]
    least = min(results)

    # least = min(least1, least2, least3, least4, least5)
    print(least)
    '''
    # I tried to make it cool but I don't have enough time.
    main()
