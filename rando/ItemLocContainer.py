
import copy, log

from smbool import SMBool
from smboolmanager import SMBoolManager
from collections import Counter

def getItemListStr(items):
    return str(dict(Counter([item.Type for item in items])))

def getLocListStr(locs):
    return str([loc['Name'] for loc in locs])

def getItemLocStr(itemLoc):
    return itemLoc['Item'].Type + " at " + itemLoc['Location']['Name']

def getItemLocationsStr(itemLocations):
    return str([getItemLocStr(il) for il in itemLocations])

class ContainerSoftBackup(object):
    def __init__(self, container):
        self.itemLocations = container.itemLocations[:]
        self.itemPool = container.itemPool[:]
        self.unusedLocations = container.unusedLocations[:]
        self.currentItems = container.currentItems[:]

    def restore(self, container, resetSM=True):
        # avoid costly deep copies of locations
        container.itemLocations = self.itemLocations[:]
        container.itemPool = self.itemPool[:]
        container.unusedLocations = self.unusedLocations[:]
        container.currentItems = self.currentItems[:]
        if resetSM:
            container.sm.resetItems()
            container.sm.addItems([it.Type for it in container.currentItems])

# Holds items yet to place (itemPool), locations yet to fill (unusedLocations),
# placed items/locations (itemLocations).
# If logic is needed, also holds a SMBoolManager (sm) and collected items so far
# (collectedItems)
class ItemLocContainer(object):
    def __init__(self, sm, itemPool, locations):
        self.sm = sm
        self.itemLocations = []
        self.unusedLocations = locations
        self.currentItems = []
        self.itemPool = itemPool
        self.itemPoolBackup = None
        self.unrestrictedItems = set()
        self.log = log.get('ItemLocContainer')
        self.checkConsistency()

    def checkConsistency(self):
        assert len(self.unusedLocations) == len(self.itemPool), "Item({})/Locs({}) count mismatch".format(len(self.itemPool), len(self.unusedLocations))

    def __eq__(self, rhs):
        eq = self.currentItems == rhs.currentItems
        eq &= getLocListStr(self.unusedLocations) == getLocListStr(rhs.unusedLocations)
        eq &= self.itemPool == rhs.itemPool
        eq &= getItemLocationsStr(self.itemLocations) == getItemLocationsStr(rhs.itemLocations)

        return eq

    def __copy__(self):
        def copyLoc(loc):
            ret = {}
            for key, value in loc.items():
                # create new smbool
                if key == 'difficulty':
                    ret[key] = SMBool(value.bool, value.difficulty, value.knows, value.items)
                else:
                    ret[key] = value
            return ret
        locs = [copyLoc(loc) for loc in self.unusedLocations]
        # we don't copy restriction state on purpose: it depends on
        # outside context we don't want to bring to the copy
        ret = ItemLocContainer(SMBoolManager(),
                               self.itemPoolBackup[:] if self.itemPoolBackup != None else self.itemPool[:],
                               locs)
        ret.currentItems = self.currentItems[:]
        ret.unrestrictedItems = copy.copy(self.unrestrictedItems)
        ret.itemLocations = [ {
            'Item': il['Item'],
            'Location': copyLoc(il['Location'])
        } for il in self.itemLocations ]
        ret.sm.addItems([item.Type for item in ret.currentItems])
        return ret

    # create a new container based on slice predicates on items and
    # locs.  both predicates must result in a consistent container
    # (same number of unused locations and not placed items)
    def slice(self, itemPoolCond, locPoolCond):
        assert self.itemPoolBackup is None, "Cannot slice a constrained container"
        locs = self.getLocs(locPoolCond)
        items = self.getItems(itemPoolCond)
        cont = ItemLocContainer(self.sm, items, locs)
        cont.currentItems = self.currentItems
        cont.itemLocations = self.itemLocations
        return copy.copy(cont)

    # transfer collected items/locations to another container
    def transferCollected(self, dest):
        dest.currentItems = self.currentItems[:]
        dest.sm = SMBoolManager()
        dest.sm.addItems([item.Type for item in dest.currentItems])
        dest.itemLocations = copy.copy(self.itemLocations)
        dest.unrestrictedItems = copy.copy(self.unrestrictedItems)

    # reset collected items/locations
    def resetCollected(self):
        self.currentItems = []
        self.itemLocations = []
        self.unrestrictedItems = set()
        self.sm.resetItems()

    def dump(self):
        return "ItemPool(%d): %s\nLocPool(%d): %s\nCollected: %s" % (len(self.itemPool), getItemListStr(self.itemPool), len(self.unusedLocations), getLocListStr(self.unusedLocations), getItemListStr(self.currentItems))

    # temporarily restrict item pool to items fulfilling predicate
    def restrictItemPool(self, predicate):
        assert self.itemPoolBackup is None, "Item pool already restricted"
        self.itemPoolBackup = self.itemPool
        self.itemPool = [item for item in self.itemPoolBackup if predicate(item)]
        self.log.debug("restrictItemPool: "+getItemListStr(self.itemPool))

    # remove a placed restriction
    def unrestrictItemPool(self):
        assert self.itemPoolBackup is not None, "No pool restriction to remove"
        self.itemPool = self.itemPoolBackup
        self.itemPoolBackup = None
        self.log.debug("unrestrictItemPool: "+getItemListStr(self.itemPool))

    # utility function that exists only because locations are lame dictionaries.
    # extract from this container locations matching the ones given
    def extractLocs(self, locs):
        ret = []
        for loc in locs:
            ret.append(next(l for l in self.unusedLocations if l['Name'] == loc['Name']))
        return ret

    def removeLocation(self, location):
        if location in self.unusedLocations:
            self.unusedLocations.remove(location)
        else:
            self.unusedLocations.remove(next(loc for loc in self.unusedLocations if loc['Name'] == location['Name']))

    def removeItem(self, item):
        self.itemPool.remove(item)
        if self.itemPoolBackup is not None:
            self.itemPoolBackup.remove(item)

    # collect an item at a location. if pickup is True, also affects logic (sm) and collectedItems
    def collect(self, itemLocation, pickup=True):
        item = itemLocation['Item']
        location = itemLocation['Location']
        if 'restricted' not in location or location['restricted'] == False:
            self.unrestrictedItems.add(item.Type)
        if pickup == True:
            self.currentItems.append(item)
            self.sm.addItem(item.Type)
        self.removeLocation(location)
        self.itemLocations.append(itemLocation)
        self.removeItem(item)

    def isPoolEmpty(self):
        return len(self.itemPool) == 0

    def getNextItemInPool(self, t):
        return next((item for item in self.itemPool if item.Type == t), None)

    def getNextItemInPoolMatching(self, predicate):
        return next((item for item in self.itemPool if predicate(item) == True), None)

    def hasItemTypeInPool(self, t):
        return any(item.Type == t for item in self.itemPool)

    def hasItemInPool(self, predicate):
        return any(predicate(item) == True for item in self.itemPool)

    def hasItemCategoryInPool(self, cat):
        return any(item.Category == cat for item in self.itemPool)

    def getNextItemInPoolFromCategory(self, cat):
        return next((item for item in self.itemPool if item.Category == cat), None)

    def getAllItemsInPoolFromCategory(self, cat):
        return [item for item in self.itemPool if item.Category == cat]

    def countItemTypeInPool(self, t):
        return sum(1 for item in self.itemPool if item.Type == t)

    def countItems(self, predicate):
        return sum(1 for item in self.itemPool if predicate(item) == True)

    # gets the items pool in the form of a dicitionary whose keys are item types
    # and values list of items of this type
    def getPoolDict(self):
        poolDict = {}
        for item in self.itemPool:
            if item.Type not in poolDict:
                poolDict[item.Type] = []
            poolDict[item.Type].append(item)
        return poolDict

    def getLocs(self, predicate):
        return [loc for loc in self.unusedLocations if predicate(loc) == True]

    def getItems(self, predicate):
        return [item for item in self.itemPool if predicate(item) == True]

    def getUsedLocs(self, predicate):
        return [il['Location'] for il in self.itemLocations if predicate(il['Location']) == True]

    def getCollectedItems(self, predicate):
        return [item for item in self.currentItems if predicate(item) == True]

    def hasUnrestrictedLocWithItemType(self, itemType):
        return itemType in self.unrestrictedItems

    def getLocsForSolver(self):
        locs = []
        for il in self.itemLocations:
            loc = il['Location']
            loc['itemName'] = il['Item'].Type
            locs.append(loc)
        return locs

    def cleanLocsAfterSolver(self):
        # restricted locs can have their difficulty set, which can cause them to be reported in the
        # post randomization warning message about locs with diff > max diff.
        for il in self.itemLocations:
            loc = il['Location']
            if loc.get('restricted') == True and loc.get('difficulty', False) == True:
                loc['difficulty'] = SMBool(False)

    def getDistinctItems(self):
        itemTypes = {item.Type for item in self.itemPool}
        return [self.getNextItemInPool(itemType) for itemType in itemTypes]
