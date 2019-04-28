import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time


class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__(self, gb, trail, val_sh, var_sh, cc):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck(self):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    def forwardChecking(self):

        for v in self.network.getVariables():

            if (v.isAssigned()):

                for neighbor in self.network.getNeighborsOfVariable(v):
                    if (neighbor.getDomain().contains(v.getAssignment())):
                        self.trail.push(neighbor)
                        neighbor.removeValueFromDomain(v.getAssignment())

        return self.network.isConsistent();

    def norvigCheck(self):

        forwardCheck = self.forwardChecking()

        if forwardCheck == False:
            return False

        for variable in self.network.getVariables():
            if variable.isAssigned() == False:
                for value in variable.getValues():
                    onlyValue = True
                    for neighbor in self.network.getConstraintsContainingVariable(variable):
                        for var in neighbor.vars:
                            if variable is not var:
                                if value in var.getValues():
                                    onlyValue = False

                    if onlyValue == True:
                        self.trail.push(variable)
                        variable.assignValue(value)
                        return self.norvigCheck()

        for variable in self.network.variables:
            if variable.domain.isEmpty() == True:
                return False

        return self.network.isConsistent()


    def getTournCC(self):
        return None

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable(self):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None


    def getMRV(self):
        temp = self.getfirstUnassignedVariable()

        for v in self.network.getVariables():
            if (v.isAssigned() == False and v.size() < temp.size()):
                temp = v

        return temp;


    def MRVwithTieBreaker(self):
        temp = self.getfirstUnassignedVariable()

        for v in self.network.getVariables():
            if (v.isAssigned() == False and v.size() < temp.size()):
                temp = v
            elif (v.isAssigned() == False and v.size() == temp.size()):
                neighborsOfV = self.network.getNeighborsOfVariable(v)
                degreeOfV = sum([1 for i in neighborsOfV if not i.isAssigned()])
                neighborsOftemp = self.network.getNeighborsOfVariable(v)
                degreeOftemp = sum([1 for i in neighborsOftemp if not i.isAssigned()])

                if (degreeOfV > degreeOftemp):
                    temp = v

        return temp;


    # Default Value Ordering
    def getValuesInOrder(self, v):
        values = v.domain.values
        return sorted(values)

    
    def getValuesLCVOrder(self, v):
        values = []
        for value in v.domain.values:
            count = 0
            for neighbor in self.network.getNeighborsOfVariable(v):
                if (neighbor.isAssigned()):
                    continue
                if (neighbor.getDomain().contains(value)):
                    count = count + 1
            values.append((value, count))

        values = sorted(values, key=lambda x: x[1])

        return [i[0] for i in values]

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve(self):
        if self.hassolution:
            return

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if (v == None):
            for var in self.network.variables:

                # If all variables haven't been assigned
                if not var.isAssigned():
                    print("Error")

            # Success
            self.hassolution = True
            return

        # Attempt to assign a value
        for i in self.getNextValues(v):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push(v)

            # Assign the value
            v.assignValue(i)

            # Propagate constraints, check consistency, recurse
            if self.checkConsistency():
                self.solve()

            # If this assignment succeeded, return
            if self.hassolution:
                return

            # Otherwise backtrack
            self.trail.undo()

    def checkConsistency(self):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable(self):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues(self, v):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder(v)

        if self.valHeuristics == "tournVal":
            return self.getTournVal(v)

        else:
            return self.getValuesInOrder(v)

    def getSolution(self):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
