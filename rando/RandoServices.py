
import log, copy, random, sys, logging
from enum import Enum, unique
from parameters import infinity
from rando.ItemLocContainer import getLocListStr, getItemListStr

class ItemWrapper(object): # to put items in dictionaries
    def __init__(self, item):
        self.item = item
        item['Wrapper'] = self

@unique
class ComebackCheckType(Enum):
    NoCheck = 1
    JustComeback = 2
    ComebackWithoutItem = 3

class RandoServices(object):
    def __init__(self, graph, restrictions, cache=None):
        self.restrictions = restrictions
        self.settings = restrictions.settings
        self.areaGraph = graph
        self.cache = cache
        self.log = log.get('RandoServices')

    def collect(self, ap, container, itemLoc):
        # walk the graph to update AP
        self.currentLocations(ap, container, itemLoc['Item'])
        container.collect(itemLoc)
        self.log.debug("COLLECT "+itemLoc['Item']['Type']+" at "+itemLoc['Location']['Name'])
        sys.stdout.write('.')
        sys.stdout.flush()
        return itemLoc['Location']['accessPoint']

    def possibleLocations(self, item, ap, emptyContainer):
        assert len(emptyContainer.currentItems) == 0, "Invalid call to possibleLocations. emptyContainer had collected items"
        allBut = emptyContainer.getItems(lambda it: it['Type'] != item['Type'])
        emptyContainer.sm.addItems([it['Type'] for it in allBut])
        ret = [loc for loc in self.currentLocations(ap, emptyContainer, post=True) if self.restrictions.canPlaceAtLocation(item, loc, emptyContainer)]
        emptyContainer.sm.resetItems()
        return ret

    def currentLocations(self, ap, container, item=None, post=False, diff=None):
        if self.cache is not None:
            request = self.cache.request('currentLocations', ap, container, None if item is None else item['Type'], post, diff)
            ret = self.cache.get(request)
            if ret is not None:
                return ret
        sm = container.sm
        if diff is None:
            diff = self.settings.maxDiff
        itemType = None
        if item is not None:
            itemType = item['Type']
            sm.addItem(itemType)
        ret = sorted(self.getAvailLocs(container, ap, diff),
                     key=lambda loc: loc['Name'])
        if post is True:
            ret = [loc for loc in ret if self.locPostAvailable(sm, loc, itemType)]
        if item is not None:
            sm.removeItem(itemType)
        if self.cache is not None:
            self.cache.store(request, ret)
        return ret

    def locPostAvailable(self, sm, loc, item):
        if not 'PostAvailable' in loc:
            return True
        result = sm.eval(loc['PostAvailable'], item)
        return result.bool == True and result.difficulty <= self.settings.maxDiff

    def getAvailLocs(self, container, ap, diff):
        sm = container.sm
        locs = container.unusedLocations
        return self.areaGraph.getAvailableLocations(locs, sm, diff, ap)

    def currentAccessPoints(self, ap, container, item=None):
        if self.cache is not None:
            request = self.cache.request('currentAccessPoints', ap, container, None if item is None else item['Type'])
            ret = self.cache.get(request)
            if ret is not None:
                return ret
        sm = container.sm
        if item is not None:
            itemType = item['Type']
            sm.addItem(itemType)
        nodes = sorted(self.areaGraph.getAvailableAccessPoints(self.areaGraph.accessPoints[ap],
                                                               sm, self.settings.maxDiff),
                       key=lambda ap: ap.Name)
        if item is not None:
            sm.removeItem(itemType)
        if self.cache is not None:
            self.cache.store(request, nodes)

        return nodes

    def isSoftlockPossible(self, container, ap, item, loc, comebackCheck):
        sm = container.sm
        # usually early game
        if comebackCheck == ComebackCheckType.NoCheck:
            return False
        # some specific checks
        if loc['Name'] == 'Bomb' or loc['Name'] == 'Mother Brain' or\
           (loc['Name'] in ['Draygon', 'Space Jump'] and sm.canExitDraygon()):
            return False
        # if the loc forces us to go to an area we can't come back from
        comeBack = loc['accessPoint'] == ap or \
            self.areaGraph.canAccess(sm, loc['accessPoint'], ap, self.settings.maxDiff, item['Type'] if item is not None else None)
        if not comeBack:
            self.log.debug("KO come back from " + loc['accessPoint'] + " to " + ap + " when trying to place " + ("None" if item is None else item['Type']) + " at " + loc['Name'])
            return True
#        else:
#            self.log.debug("OK come back from " + loc['accessPoint'] + " to " + ap + " when trying to place " + item['Type'] + " at " + loc['Name'])
        if item is not None and comebackCheck == ComebackCheckType.ComebackWithoutItem and self.isProgression(item, ap, container):
            # we know that loc is avail and post avail with the item
            # if it is not post avail without it, then the item prevents the
            # possible softlock
            if not self.locPostAvailable(sm, loc, None):
                return True
            # item allows us to come back from a softlock possible zone
            comeBackWithout = self.areaGraph.canAccess(sm, loc['accessPoint'],
                                                       ap,
                                                       self.settings.maxDiff,
                                                       None)
            if not comeBackWithout:
                return True

        return False

    def fullComebackCheck(self, container, ap, item, loc, comebackCheck):
        sm = container.sm
        return self.locPostAvailable(sm, loc, item['Type'] if item is not None else None) and not self.isSoftlockPossible(container, ap, item, loc, comebackCheck)

    def isProgression(self, item, ap, container):
        sm = container.sm
        # no need to test nothing items
        if item['Category'] == 'Nothing' or item['Category'] == 'Boss':
            return False
        if self.cache is not None:
            request = self.cache.request('isProgression', item['Type'], ap, container)
            ret = self.cache.get(request)
            if ret is not None:
                return ret
        oldLocations = self.currentLocations(ap, container)
        ret = any(self.restrictions.canPlaceAtLocation(item, loc, container) for loc in oldLocations)
        if ret == True:
            newLocations = [loc for loc in self.currentLocations(ap, container, item) if loc not in oldLocations]
            ret = len(newLocations) > 0 and any(self.restrictions.isItemLocMatching(item, loc) for loc in newLocations)
            self.log.debug('isProgression. item=' + item['Type'] + ', newLocs=' + str([loc['Name'] for loc in newLocations]))
            if ret == False and len(newLocations) > 0 and self.restrictions.split == 'Major':
                # in major/minor split, still consider minor locs as
                # progression if not all types are distributed
                ret = not sm.haveItem('Missile').bool \
                      or not sm.haveItem('Super').bool \
                      or not sm.haveItem('PowerBomb').bool
        if self.cache is not None:
            self.cache.store(request, ret)
        return ret

    def getPlacementLocs(self, ap, container, comebackCheck, itemObj, locs):
        return [loc for loc in locs if (itemObj is None or self.restrictions.canPlaceAtLocation(itemObj, loc, container)) and self.fullComebackCheck(container, ap, itemObj, loc, comebackCheck)]

    def processEarlyMorph(self, ap, container, comebackCheck, itemLocDict, curLocs):
        morph = container.getNextItemInPool('Morph')
        if morph is not None:
            self.log.debug("getPossiblePlacements: early morph check - morph not placed yet")
            morphWrapper = next((w for w in itemLocDict if w.item['Type'] == morph['Type']), None)
            if morphWrapper is not None:
                morphLocs = itemLocDict[morphWrapper]
                itemLocDict.clear()
                itemLocDict[morphWrapper] = morphLocs
            elif len(curLocs) >= 2:
                self.log.debug("getPossiblePlacements: early morph placement check")
                # we have to place morph early, it's still not placed, and not detected as placeable
                # let's see if we can place it anyway in the context of a combo
                morphLocs = self.getPlacementLocs(ap, container, comebackCheck, morph, curLocs)
                if len(morphLocs) > 0:
                    # copy our context to do some destructive checks
                    containerCpy = copy.copy(container)
                    # choose a morph item location in that context
                    morphItemLoc = {
                        'Item':morph,
                        'Location':random.choice(containerCpy.extractLocs(morphLocs))
                    }
                    # acquire morph in new context and see if we can still open new locs
                    newAP = self.collect(ap, container, morphItemLoc)
                    (ild, poss) = self.getPossiblePlacements(newAP, containerCpy, comebackCheck)
                    if poss:
                        # it's possible, only offer morph as possibility
                        itemLocDict.clear()
                        itemLocDict[ItemWrapper(morph)] = morphLocs

    def processLateMorph(self, container, itemLocDict):
        morphWrapper = next((w for w in itemLocDict if w.item['Type'] == 'Morph'), None)
        if morphWrapper is None or len(itemLocDict) == 1:
            # no morph, or it is the only possibility: nothing to do
            return
        forbidden = not self.restrictions.lateMorphCheck(container)
        if not forbidden and self.restrictions.lateMorphForbiddenArea is not None:
            morphLocs = [loc for loc in itemLocDict[morphWrapper] if loc['GraphArea'] != self.restrictions.lateMorphForbiddenArea]
            forbidden = len(morphLocs) == 0
            if not forbidden:
                itemLocDict[morphWrapper] = morphLocs
        if forbidden:
            del itemLocDict[morphWrapper]

    def processMorphPlacements(self, ap, container, comebackCheck, itemLocDict, curLocs):
        if self.restrictions.isEarlyMorph():
            self.processEarlyMorph(ap, container, comebackCheck, itemLocDict, curLocs)
        elif self.restrictions.isLateMorph():
            self.processLateMorph(container, itemLocDict)

    def getPossiblePlacements(self, ap, container, comebackCheck):
        curLocs = self.currentLocations(ap, container)
        self.log.debug('getPossiblePlacements. nCurLocs='+str(len(curLocs)))
        self.log.debug('getPossiblePlacements. curLocs='+getLocListStr(curLocs))
        sm = container.sm
        poolDict = container.getPoolDict()
        itemLocDict = {}
        possibleProg = False
        nonProgList = None
        def getLocList(itemObj):
            nonlocal curLocs
            return self.getPlacementLocs(ap, container, comebackCheck, itemObj, curLocs)
        def getNonProgLocList(itemObj):
            nonlocal nonProgList
            if nonProgList is None:
                nonProgList = [loc for loc in self.currentLocations(ap, container) if self.fullComebackCheck(container, ap, itemObj, loc, comebackCheck)] # we don't care what the item is
                self.log.debug("nonProgLocList="+str([loc['Name'] for loc in nonProgList]))
            return [loc for loc in nonProgList if self.restrictions.canPlaceAtLocation(itemObj, loc, container)]
        # boss handling : check if we can kill a boss, if so return immediately
        hasBoss = container.hasItemCategoryInPool('Boss')
        bossLoc = None if not hasBoss else next((loc for loc in curLocs if 'Boss' in loc['Class'] and self.fullComebackCheck(container, ap, None, loc, comebackCheck)), None)
        if bossLoc is not None:
            bosses = container.getItems(lambda item: item['Name'] == bossLoc['Name'])
            assert len(bosses) == 1
            boss = bosses[0]
            itemLocDict[ItemWrapper(boss)] = [bossLoc]
            self.log.debug("getPossiblePlacements. boss: "+boss['Name'])
            return (itemLocDict, False)
        for itemType,items in sorted(poolDict.items()):
            itemObj = items[0]
            cont = True
            prog = False
            if self.isProgression(itemObj, ap, container):
                cont = False
                prog = True
            elif not possibleProg:
                cont = False
            if cont: # ignore non prog items if a prog item has already been found
                continue
            # check possible locations for this item type
#            self.log.debug('getPossiblePlacements. itemType=' + itemType + ', curLocs='+str([loc['Name'] for loc in curLocs]))
            locations = getLocList(itemObj) if prog else getNonProgLocList(itemObj)
            if len(locations) == 0:
                continue
            if prog and not possibleProg:
                possibleProg = True
                itemLocDict = {} # forget all the crap ones we stored just in case
#            self.log.debug('getPossiblePlacements. itemType=' + itemType + ', locs='+str([loc['Name'] for loc in locations]))
            for item in items:
                itemLocDict[ItemWrapper(item)] = locations
        self.processMorphPlacements(ap, container, comebackCheck, itemLocDict, curLocs)
        if self.log.getEffectiveLevel() == logging.DEBUG:
            debugDict = {}
            for w, locList in itemLocDict.items():
                if w.item['Type'] not in debugDict:
                    debugDict[w.item['Type']] = [loc['Name'] for loc in locList]
            self.log.debug('itemLocDict='+str(debugDict))
            self.log.debug('possibleProg='+str(possibleProg))
        return (itemLocDict, possibleProg)

    def getPossiblePlacementsNoLogic(self, container):
        poolDict = container.getPoolDict()
        itemLocDict = {}
        def getLocList(itemObj, baseList):
            return [loc for loc in baseList if self.restrictions.canPlaceAtLocation(itemObj, loc, container)]
        for itemType,items in sorted(poolDict.items()):
            itemObj = items[0]
            locList = getLocList(itemObj, container.unusedLocations)
            for item in items:
                itemLocDict[ItemWrapper(item)] = locList
        return (itemLocDict, False)

    # check if bosses are blocking the last remaining locations.
    # accurate most of the time, still a heuristic
    def onlyBossesLeft(self, ap, container):
        if self.settings.maxDiff == infinity:
            return False
        self.log.debug('onlyBossesLeft, diff=' + str(self.settings.maxDiff) + ", ap="+ap)
        sm = container.sm
        bossesLeft = container.getAllItemsInPoolFromCategory('Boss')
        if len(bossesLeft) == 0:
            return False
        def getLocList():
            curLocs = self.currentLocations(ap, container)
            self.log.debug('onlyBossesLeft, curLocs=' + getLocListStr(curLocs))
            return self.getPlacementLocs(ap, container, ComebackCheckType.JustComeback, None, curLocs)
        prevLocs = getLocList()
        self.log.debug("onlyBossesLeft. prevLocs="+getLocListStr(prevLocs))
        # fake kill remaining bosses and see if we can access the rest of the game
        if self.cache is not None:
            self.cache.reset()
        for boss in bossesLeft:
            self.log.debug('onlyBossesLeft. kill '+boss['Name'])
            sm.addItem(boss['Type'])
        # get bosses locations and newly accessible locations (for bosses that open up locs)
        newLocs = getLocList()
        self.log.debug("onlyBossesLeft. newLocs="+getLocListStr(newLocs))
        locs = newLocs + container.getLocs(lambda loc: 'Boss' in loc['Class'] and not loc in newLocs)
        self.log.debug("onlyBossesLeft. locs="+getLocListStr(locs))
        ret = (len(locs) > len(prevLocs) and len(locs) == len(container.unusedLocations))
        # restore bosses killed state
        for boss in bossesLeft:
            self.log.debug('onlyBossesLeft. revive '+boss['Name'])
            sm.removeItem(boss['Type'])
        if self.cache is not None:
            self.cache.reset()
        self.log.debug("onlyBossesLeft? " +str(ret))
        return ret

    def canEndGame(self, container):
        return not any(loc['Name'] == 'Mother Brain' for loc in container.unusedLocations)

    # def couldEndGame(self, container):