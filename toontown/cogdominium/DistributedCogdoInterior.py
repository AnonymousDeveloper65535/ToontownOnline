# File: t (Python 2.4)

import random
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.building.ElevatorConstants import *
from toontown.toon import NPCToons
from pandac.PandaModules import NodePath
from toontown.building import ElevatorUtils
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
from direct.fsm import State
from direct.fsm.StatePush import StateVar, FunctionCall
from toontown.battle import BattleBase
from toontown.hood import ZoneUtil
from toontown.cogdominium.CogdoLayout import CogdoLayout
from toontown.cogdominium import CogdoGameConsts
from toontown.cogdominium import CogdoBarrelRoom, CogdoBarrelRoomConsts
from toontown.distributed import DelayDelete
from toontown.toonbase import TTLocalizer
from CogdoExecutiveSuiteMovies import CogdoExecutiveSuiteIntro
from CogdoElevatorMovie import CogdoElevatorMovie
PAINTING_DICT = {
    's': 'tt_m_ara_crg_paintingMoverShaker',
    'l': 'tt_m_ara_crg_paintingLegalEagle',
    'm': 'tt_m_ara_crg_paintingMoverShaker',
    'c': 'tt_m_ara_crg_paintingMoverShaker' }

class DistributedCogdoInterior(DistributedObject.DistributedObject):
    id = 0
    cageHeights = [
        11.359999999999999,
        0.01]
    
    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.toons = []
        self.activeIntervals = { }
        self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.mp3')
        self.closeSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_close.mp3')
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.distBldgDoId = None
        self._CogdoGameRepeat = config.GetBool('cogdo-game-repeat', 0)
        self.currentFloor = -1
        self.elevatorName = self._DistributedCogdoInterior__uniqueName('elevator')
        self.floorModel = None
        self.elevatorOutOpen = 0
        self.BottomFloor_SuitPositions = [
            Point3(0, 15, 0),
            Point3(10, 20, 0),
            Point3(-7, 24, 0),
            Point3(-10, 0, 0)]
        self.BottomFloor_SuitHs = [
            75,
            170,
            -91,
            -44]
        self.Cubicle_SuitPositions = [
            Point3(0, 18, 0),
            Point3(10, 12, 0),
            Point3(-9, 11, 0),
            Point3(-3, 13, 0)]
        self.Cubicle_SuitHs = [
            170,
            56,
            -52,
            10]
        self.BossOffice_SuitPositions = [
            Point3(0, 15, 0),
            Point3(10, 20, 0),
            Point3(-10, 6, 0),
            Point3(-17, 30, 0)]
        self.BossOffice_SuitHs = [
            170,
            120,
            12,
            38]
        self._wantBarrelRoom = config.GetBool('cogdo-want-barrel-room', 0)
        self.barrelRoom = CogdoBarrelRoom.CogdoBarrelRoom()
        self.brResults = [
            [],
            []]
        self.barrelRoomIntroTrack = None
        self.penthouseOutroTrack = None
        self.penthouseOutroChatDoneTrack = None
        self.penthouseIntroTrack = None
        self.waitMusic = base.loadMusic('phase_7/audio/bgm/encntr_toon_winning_indoor.mid')
        self.elevatorMusic = base.loadMusic('phase_7/audio/bgm/tt_elevator.mid')
        self.fsm = ClassicFSM.ClassicFSM('DistributedCogdoInterior', [
            State.State('WaitForAllToonsInside', self.enterWaitForAllToonsInside, self.exitWaitForAllToonsInside, [
                'Elevator']),
            State.State('Elevator', self.enterElevator, self.exitElevator, [
                'Game']),
            State.State('Game', self.enterGame, self.exitGame, [
                'Resting',
                'Failed',
                'BattleIntro']),
            State.State('BarrelRoomIntro', self.enterBarrelRoomIntro, self.exitBarrelRoomIntro, [
                'CollectBarrels',
                'Off']),
            State.State('CollectBarrels', self.enterCollectBarrels, self.exitCollectBarrels, [
                'BarrelRoomReward',
                'Off']),
            State.State('BarrelRoomReward', self.enterBarrelRoomReward, self.exitBarrelRoomReward, [
                'Battle',
                'ReservesJoining',
                'BattleIntro',
                'Off']),
            State.State('BattleIntro', self.enterBattleIntro, self.exitBattleIntro, [
                'Battle',
                'ReservesJoining',
                'Off']),
            State.State('Battle', self.enterBattle, self.exitBattle, [
                'Resting',
                'Reward',
                'ReservesJoining']),
            State.State('ReservesJoining', self.enterReservesJoining, self.exitReservesJoining, [
                'Battle']),
            State.State('Resting', self.enterResting, self.exitResting, [
                'Elevator']),
            State.State('Reward', self.enterReward, self.exitReward, [
                'Off']),
            State.State('Failed', self.enterFailed, self.exitFailed, [
                'Off']),
            State.State('Off', self.enterOff, self.exitOff, [
                'Elevator',
                'WaitForAllToonsInside',
                'Battle'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self._haveEntranceElevator = StateVar(False)
        self._stashEntranceElevator = StateVar(False)
        self._stashEntranceElevatorFC = FunctionCall(self._doStashEntranceElevator, self._haveEntranceElevator, self._stashEntranceElevator)
        self._entranceElevCallbacks = []
        self._doEntranceElevCallbacksFC = FunctionCall(self._doEntranceElevCallbacks, self._haveEntranceElevator)
        self.cage = None
        self.shopOwnerNpcId = None
        self.shopOwnerNpc = None
        self._movie = None
        self.SOSToonName = None
        self.FOType = None

    
    def setShopOwnerNpcId(self, npcId):
        self.shopOwnerNpcId = npcId

    
    def setSOSNpcId(self, npcId):
        self.SOSToonName = NPCToons.getNPCName(npcId)

    
    def setFOType(self, typeId):
        self.FOType = chr(typeId)

    
    def _DistributedCogdoInterior__uniqueName(self, name):
        DistributedCogdoInterior.id += 1
        return name + '%d' % DistributedCogdoInterior.id

    
    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.announceGenerateName = self.uniqueName('generate')
        self.accept(self.announceGenerateName, self.handleAnnounceGenerate)
        self.elevatorModelIn = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_csa_elevatorB')
        self.leftDoorIn = self.elevatorModelIn.find('**/left_door')
        self.rightDoorIn = self.elevatorModelIn.find('**/right_door')
        self.elevatorModelOut = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_csa_elevatorB')
        self.leftDoorOut = self.elevatorModelOut.find('**/left_door')
        self.rightDoorOut = self.elevatorModelOut.find('**/right_door')

    
    def _DistributedCogdoInterior__makeShopOwnerNpc(self):
        if self.shopOwnerNpc:
            return None
        
        self.shopOwnerNpc = NPCToons.createLocalNPC(self.shopOwnerNpcId)
        if not self.shopOwnerNpc:
            self.notify.warning('No shopkeeper in this cogdominium, using FunnyFarm Sellbot FO NPCToons')
            random.seed(self.doId)
            shopkeeper = random.randint(7001, 7009)
            self.shopOwnerNpc = NPCToons.createLocalNPC(shopkeeper)
        
        self.shopOwnerNpc.addActive()
        self.shopOwnerNpc.reparentTo(self.cage)
        self.shopOwnerNpc.setPosHpr(0, -2, 0, 180, 0, 0)
        self.shopOwnerNpc.loop('neutral')

    
    def setElevatorLights(self, elevatorModel):
        npc = elevatorModel.findAllMatches('**/floor_light_?;+s')
        for i in range(npc.getNumPaths()):
            np = npc.getPath(i)
            floor = int(np.getName()[-1:]) - 1
            if floor == self.currentFloor:
                np.setColor(LIGHT_ON_COLOR)
                continue
            if floor < self.layout.getNumGameFloors():
                if self.isBossFloor(self.currentFloor):
                    np.setColor(LIGHT_ON_COLOR)
                else:
                    np.setColor(LIGHT_OFF_COLOR)
            self.isBossFloor(self.currentFloor)
            np.hide()
        

    
    def startAlertElevatorLightIval(self, elevatorModel):
        light = elevatorModel.find('**/floor_light_%s' % (self.currentFloor + 1))
        track = Sequence(Func(light.setColor, Vec4(1.0, 0.59999999999999998, 0.59999999999999998, 1.0)), Wait(0.90000000000000002), Func(light.setColor, LIGHT_ON_COLOR), Wait(0.90000000000000002))
        self.activeIntervals['alertElevatorLight'] = track
        track.loop()

    
    def stopAlertElevatorLightIval(self, elevatorModel):
        self._DistributedCogdoInterior__finishInterval('alertElevatorLight')
        self.setElevatorLights(elevatorModel)

    
    def handleAnnounceGenerate(self, obj):
        self.ignore(self.announceGenerateName)
        self.cageDoorSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_door.mp3')
        self.cageLowerSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_lower.mp3')
        self.sendUpdate('setAvatarJoined', [])

    
    def disable(self):
        self.fsm.requestFinalState()
        self._DistributedCogdoInterior__cleanupIntervals()
        self.ignoreAll()
        self._DistributedCogdoInterior__cleanup()
        self._DistributedCogdoInterior__cleanupShopOwnerNpc()
        self._DistributedCogdoInterior__cleanupPenthouseIntro()
        DistributedObject.DistributedObject.disable(self)

    
    def _DistributedCogdoInterior__cleanupShopOwnerNpc(self):
        if self.shopOwnerNpc:
            self.shopOwnerNpc.removeActive()
            self.shopOwnerNpc.delete()
            self.shopOwnerNpc = None
        

    
    def _DistributedCogdoInterior__cleanupPenthouseIntro(self):
        if hasattr(self, '_movie') and self._movie:
            self._movie.unload()
            self._movie = None
        

    
    def delete(self):
        self._stashEntranceElevatorFC.destroy()
        self._doEntranceElevCallbacksFC.destroy()
        self._haveEntranceElevator.destroy()
        self._stashEntranceElevator.destroy()
        self._entranceElevCallbacks = None
        del self.waitMusic
        del self.elevatorMusic
        del self.openSfx
        del self.closeSfx
        del self.fsm
        base.localAvatar.inventory.setBattleCreditMultiplier(1)
        DistributedObject.DistributedObject.delete(self)

    
    def isBossFloor(self, floorNum):
        if self.layout.hasBossBattle():
            if self.layout.getBossBattleFloor() == floorNum:
                return True
            
        
        return False

    
    def _DistributedCogdoInterior__cleanup(self):
        self.toons = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        if self.elevatorModelIn != None:
            self.elevatorModelIn.removeNode()
        
        if self.elevatorModelOut != None:
            self.elevatorModelOut.removeNode()
        
        if self.floorModel != None:
            self.floorModel.removeNode()
        
        if self.cage != None:
            self.cage = None
        
        if self.barrelRoom != None:
            self.barrelRoom.destroy()
            self.barrelRoom = None
        
        self.leftDoorIn = None
        self.rightDoorIn = None
        self.leftDoorOut = None
        self.rightDoorOut = None

    
    def _DistributedCogdoInterior__addToon(self, toon):
        self.accept(toon.uniqueName('disable'), self._DistributedCogdoInterior__handleUnexpectedExit, extraArgs = [
            toon])

    
    def _DistributedCogdoInterior__handleUnexpectedExit(self, toon):
        self.notify.warning('handleUnexpectedExit() - toon: %d' % toon.doId)
        self._DistributedCogdoInterior__removeToon(toon, unexpected = 1)

    
    def _DistributedCogdoInterior__removeToon(self, toon, unexpected = 0):
        if self.toons.count(toon) == 1:
            self.toons.remove(toon)
        
        self.ignore(toon.uniqueName('disable'))

    
    def _DistributedCogdoInterior__finishInterval(self, name):
        if self.activeIntervals.has_key(name):
            interval = self.activeIntervals[name]
            if interval.isPlaying():
                interval.finish()
            
        

    
    def _DistributedCogdoInterior__cleanupIntervals(self):
        for interval in self.activeIntervals.values():
            interval.finish()
        
        self.activeIntervals = { }

    
    def _DistributedCogdoInterior__closeInElevator(self):
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)

    
    def getZoneId(self):
        return self.zoneId

    
    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    
    def getExtZoneId(self):
        return self.extZoneId

    
    def setExtZoneId(self, extZoneId):
        self.extZoneId = extZoneId

    
    def getDistBldgDoId(self):
        return self.distBldgDoId

    
    def setDistBldgDoId(self, distBldgDoId):
        self.distBldgDoId = distBldgDoId

    
    def setNumFloors(self, numFloors):
        self.layout = CogdoLayout(numFloors)

    
    def getToonIds(self):
        toonIds = []
        for toon in self.toons:
            toonIds.append(toon.doId)
        
        return toonIds

    
    def setToons(self, toonIds, hack):
        self.toonIds = toonIds
        oldtoons = self.toons
        self.toons = []
        for toonId in toonIds:
            if toonId != 0:
                if self.cr.doId2do.has_key(toonId):
                    toon = self.cr.doId2do[toonId]
                    toon.stopSmooth()
                    self.toons.append(toon)
                    if oldtoons.count(toon) == 0:
                        self._DistributedCogdoInterior__addToon(toon)
                    
                else:
                    self.notify.warning('setToons() - no toon: %d' % toonId)
            self.cr.doId2do.has_key(toonId)
        
        for toon in oldtoons:
            if self.toons.count(toon) == 0:
                self._DistributedCogdoInterior__removeToon(toon)
                continue
        

    
    def setSuits(self, suitIds, reserveIds, values):
        oldsuits = self.suits
        self.suits = []
        self.joiningReserves = []
        for suitId in suitIds:
            if self.cr.doId2do.has_key(suitId):
                suit = self.cr.doId2do[suitId]
                self.suits.append(suit)
                suit.fsm.request('Battle')
                suit.buildingSuit = 1
                suit.reparentTo(render)
                if oldsuits.count(suit) == 0:
                    self.joiningReserves.append(suit)
                
            oldsuits.count(suit) == 0
            self.notify.warning('setSuits() - no suit: %d' % suitId)
        
        self.reserveSuits = []
        for index in range(len(reserveIds)):
            suitId = reserveIds[index]
            if self.cr.doId2do.has_key(suitId):
                suit = self.cr.doId2do[suitId]
                self.reserveSuits.append((suit, values[index]))
                continue
            self.notify.warning('setSuits() - no suit: %d' % suitId)
        
        if len(self.joiningReserves) > 0:
            self.fsm.request('ReservesJoining')
        

    
    def setState(self, state, timestamp):
        self.fsm.request(state, [
            globalClockDelta.localElapsedTime(timestamp)])

    
    def stashElevatorIn(self, stash = True):
        self._stashEntranceElevator.set(stash)

    
    def getEntranceElevator(self, callback):
        if self._haveEntranceElevator.get():
            callback(self.elevIn)
        else:
            self._entranceElevCallbacks.append(callback)

    
    def _doEntranceElevCallbacks(self, haveElev):
        if haveElev:
            while len(self._entranceElevCallbacks):
                cbs = self._entranceElevCallbacks[:]
                self._entranceElevCallbacks = []
                for callback in cbs:
                    callback(self.elevIn)
                
        

    
    def _doStashEntranceElevator(self, haveElev, doStash):
        if haveElev:
            if doStash:
                self.elevIn.stash()
            else:
                self.elevIn.unstash()
        

    
    def d_elevatorDone(self):
        self.sendUpdate('elevatorDone', [])

    
    def d_reserveJoinDone(self):
        self.sendUpdate('reserveJoinDone', [])

    
    def enterOff(self, ts = 0):
        messenger.send('sellbotFieldOfficeChanged', [
            False])

    
    def exitOff(self):
        pass

    
    def enterWaitForAllToonsInside(self, ts = 0):
        base.transitions.fadeOut(0)

    
    def exitWaitForAllToonsInside(self):
        pass

    
    def enterGame(self, ts = 0):
        base.cr.forbidCheesyEffects(1)

    
    def exitGame(self):
        base.cr.forbidCheesyEffects(0)

    
    def _DistributedCogdoInterior__playElevator(self, ts, name, callback):
        SuitHs = []
        SuitPositions = []
        if self.floorModel:
            self.floorModel.removeNode()
            self.floorModel = None
        
        if self.cage:
            self.cage = None
        
        if self.currentFloor == 0:
            SuitHs = self.BottomFloor_SuitHs
            SuitPositions = self.BottomFloor_SuitPositions
        
        if self.isBossFloor(self.currentFloor):
            self.barrelRoom.unload()
            self.floorModel = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_crg_penthouse')
            self.cage = self.floorModel.find('**/cage')
            pos = self.cage.getPos()
            self.cagePos = []
            for height in self.cageHeights:
                self.cagePos.append(Point3(pos[0], pos[1], height))
            
            self.cageDoor = self.floorModel.find('**/cage_door')
            self.cageDoor.wrtReparentTo(self.cage)
            if self.FOType:
                paintingModelName = PAINTING_DICT.get(self.FOType)
                for i in range(4):
                    paintingModel = loader.loadModel('phase_5/models/cogdominium/%s' % paintingModelName)
                    loc = self.floorModel.find('**/loc_painting%d' % (i + 1))
                    paintingModel.reparentTo(loc)
                
            
            SuitHs = self.BossOffice_SuitHs
            SuitPositions = self.BossOffice_SuitPositions
            self._DistributedCogdoInterior__makeShopOwnerNpc()
        elif self._wantBarrelRoom:
            self.barrelRoom.load()
            self.barrelRoom.hide()
        
        SuitHs = self.Cubicle_SuitHs
        SuitPositions = self.Cubicle_SuitPositions
        if self.floorModel:
            self.floorModel.reparentTo(render)
            if self.isBossFloor(self.currentFloor):
                self.notify.debug('Load boss_suit_office')
                elevIn = self.floorModel.find(CogdoGameConsts.PenthouseElevatorInPath).copyTo(render)
                elevOut = self.floorModel.find(CogdoGameConsts.PenthouseElevatorOutPath)
                frame = self.elevatorModelOut.find('**/frame')
                if not frame.isEmpty():
                    frame.hide()
                
                frame = self.elevatorModelIn.find('**/frame')
                if not frame.isEmpty():
                    frame.hide()
                
                self.elevatorModelOut.reparentTo(elevOut)
            else:
                elevIn = self.floorModel.find('**/elevator-in')
                elevOut = self.floorModel.find('**/elevator-out')
        elif self._wantBarrelRoom and self.barrelRoom.isLoaded():
            elevIn = self.barrelRoom.dummyElevInNode
            elevOut = self.barrelRoom.model.find(CogdoBarrelRoomConsts.BarrelRoomElevatorOutPath)
            y = elevOut.getY(render)
            elevOut = elevOut.copyTo(render)
            elevOut.setY(render, y - 0.75)
        else:
            floorModel = loader.loadModel('phase_7/models/modules/boss_suit_office')
            elevIn = floorModel.find('**/elevator-in').copyTo(render)
            elevOut = floorModel.find('**/elevator-out').copyTo(render)
            floorModel.removeNode()
        self.elevIn = elevIn
        self.elevOut = elevOut
        self._haveEntranceElevator.set(True)
        for index in range(len(self.suits)):
            self.suits[index].setPos(SuitPositions[index])
            if len(self.suits) > 2:
                self.suits[index].setH(SuitHs[index])
            else:
                self.suits[index].setH(170)
            self.suits[index].loop('neutral')
        
        for toon in self.toons:
            toon.reparentTo(self.elevatorModelIn)
            index = self.toonIds.index(toon.doId)
            toon.setPos(ElevatorPoints[index][0], ElevatorPoints[index][1], ElevatorPoints[index][2])
            toon.setHpr(180, 0, 0)
            toon.loop('neutral')
        
        self.elevatorModelIn.reparentTo(elevIn)
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)
        camera.reparentTo(self.elevatorModelIn)
        camera.setH(180)
        camera.setP(0)
        camera.setPos(0, 14, 4)
        base.playMusic(self.elevatorMusic, looping = 1, volume = 0.80000000000000004)
        track = Sequence(Func(base.transitions.noTransitions), ElevatorUtils.getRideElevatorInterval(ELEVATOR_NORMAL), ElevatorUtils.getOpenInterval(self, self.leftDoorIn, self.rightDoorIn, self.openSfx, None, type = ELEVATOR_NORMAL), Func(camera.wrtReparentTo, render))
        for toon in self.toons:
            track.append(Func(toon.wrtReparentTo, render))
        
        track.append(Func(callback))
        track.start(ts)
        self.activeIntervals[name] = track

    
    def enterElevator(self, ts = 0):
        if not self._CogdoGameRepeat:
            self.currentFloor += 1
        
        self.cr.playGame.getPlace().currentFloor = self.currentFloor
        self.setElevatorLights(self.elevatorModelIn)
        self.setElevatorLights(self.elevatorModelOut)
        if not self.isBossFloor(self.currentFloor):
            self.elevatorModelOut.detachNode()
            messenger.send('sellbotFieldOfficeChanged', [
                True])
        else:
            self._movie = CogdoElevatorMovie()
            self._movie.load()
            self._movie.play()
        self._DistributedCogdoInterior__playElevator(ts, self.elevatorName, self._DistributedCogdoInterior__handleElevatorDone)
        mult = ToontownBattleGlobals.getCreditMultiplier(self.currentFloor)
        base.localAvatar.inventory.setBattleCreditMultiplier(mult)

    
    def _DistributedCogdoInterior__handleElevatorDone(self):
        self.d_elevatorDone()

    
    def exitElevator(self):
        self.elevatorMusic.stop()
        if self._movie:
            self._movie.end()
            self._DistributedCogdoInterior__cleanupPenthouseIntro()
        
        self._DistributedCogdoInterior__finishInterval(self.elevatorName)

    
    def _DistributedCogdoInterior__setupBarrelRoom(self):
        base.cr.playGame.getPlace().fsm.request('stopped')
        base.transitions.irisOut(0.0)
        self.elevatorModelIn.detachNode()
        self._showExitElevator()
        self.barrelRoom.show()
        self.barrelRoom.placeToonsAtEntrance(self.toons)

    
    def barrelRoomIntroDone(self):
        self.sendUpdate('toonBarrelRoomIntroDone', [])

    
    def enterBarrelRoomIntro(self, ts = 0):
        if not self.isBossFloor(self.currentFloor):
            if self._wantBarrelRoom:
                self._DistributedCogdoInterior__setupBarrelRoom()
                (self.barrelRoomIntroTrack, trackName) = self.barrelRoom.getIntroInterval()
                self.barrelRoomIntroDoneEvent = trackName
                self.accept(self.barrelRoomIntroDoneEvent, self.barrelRoomIntroDone)
                self.activeIntervals[trackName] = self.barrelRoomIntroTrack
                self.barrelRoomIntroTrack.start(ts)
            else:
                self._showExitElevator()
        

    
    def exitBarrelRoomIntro(self):
        if self._wantBarrelRoom and not self.isBossFloor(self.currentFloor):
            self.ignore(self.barrelRoomIntroDoneEvent)
            if self.barrelRoomIntroTrack:
                self.barrelRoomIntroTrack.finish()
                DelayDelete.cleanupDelayDeletes(self.barrelRoomIntroTrack)
                self.barrelRoomIntroTrack = None
            
        

    
    def _DistributedCogdoInterior__handleLocalToonLeftBarrelRoom(self):
        self.notify.info('Local toon teleported out of barrel room.')
        self.sendUpdate('toonLeftBarrelRoom', [])
        self.barrelRoom.deactivate()

    
    def enterCollectBarrels(self, ts = 0):
        if not self.isBossFloor(self.currentFloor):
            if self._wantBarrelRoom:
                self.acceptOnce('localToonLeft', self._DistributedCogdoInterior__handleLocalToonLeftBarrelRoom)
                self.barrelRoom.activate()
                base.playMusic(self.waitMusic, looping = 1, volume = 0.69999999999999996)
            
        

    
    def exitCollectBarrels(self):
        if self._wantBarrelRoom and not self.isBossFloor(self.currentFloor):
            self.ignore('localToonLeft')
            self.barrelRoom.deactivate()
            self.waitMusic.stop()
        

    
    def _DistributedCogdoInterior__brRewardDone(self, task = None):
        self.notify.info('Toon finished watching the barrel room reward.')
        self.sendUpdate('toonBarrelRoomRewardDone', [])

    
    def setBarrelRoomReward(self, avIds, laffs):
        self.brResults = [
            avIds,
            laffs]
        self.barrelRoom.setRewardResults(self.brResults)

    
    def enterBarrelRoomReward(self, ts = 0):
        if self._wantBarrelRoom and not self.isBossFloor(self.currentFloor):
            base.cr.playGame.getPlace().fsm.request('stopped')
            self.startAlertElevatorLightIval(self.elevatorModelOut)
            (track, trackName) = self.barrelRoom.showRewardUi(self.brResults, callback = self._DistributedCogdoInterior__brRewardDone)
            self.activeIntervals[trackName] = track
            track.start()
            self.barrelRoom.placeToonsNearBattle(self.toons)
        

    
    def exitBarrelRoomReward(self):
        if self._wantBarrelRoom and not self.isBossFloor(self.currentFloor):
            base.cr.playGame.getPlace().fsm.request('walk')
            self.stopAlertElevatorLightIval(self.elevatorModelOut)
            self.barrelRoom.hideRewardUi()
        

    
    def enterBattleIntro(self, ts = 0):
        self._movie = CogdoExecutiveSuiteIntro(self.shopOwnerNpc)
        self._movie.load()
        self._movie.play()

    
    def exitBattleIntro(self):
        self._movie.end()
        self._DistributedCogdoInterior__cleanupPenthouseIntro()

    
    def _DistributedCogdoInterior__playCloseElevatorOut(self, name, delay = 0):
        track = Sequence(Wait(delay + SUIT_LEAVE_ELEVATOR_TIME), Parallel(SoundInterval(self.closeSfx), LerpPosInterval(self.leftDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL), startPos = Point3(0, 0, 0), blendType = 'easeOut'), LerpPosInterval(self.rightDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL), startPos = Point3(0, 0, 0), blendType = 'easeOut')))
        track.start()
        self.activeIntervals[name] = track

    
    def enterBattle(self, ts = 0):
        if self._wantBarrelRoom and self.elevatorOutOpen == 1:
            self._DistributedCogdoInterior__playCloseElevatorOut(self.uniqueName('close-out-elevator'), delay = 2)
            camera.setPos(0, -15, 6)
            camera.headsUp(self.elevatorModelOut)
        

    
    def _showExitElevator(self):
        self.elevatorModelOut.reparentTo(self.elevOut)
        self.leftDoorOut.setPos(3.5, 0, 0)
        self.rightDoorOut.setPos(-3.5, 0, 0)
        if not (self._wantBarrelRoom) and self.elevatorOutOpen == 1:
            self._DistributedCogdoInterior__playCloseElevatorOut(self.uniqueName('close-out-elevator'))
            camera.setPos(0, -15, 6)
            camera.headsUp(self.elevatorModelOut)
        

    
    def exitBattle(self):
        if self.elevatorOutOpen == 1:
            self._DistributedCogdoInterior__finishInterval(self.uniqueName('close-out-elevator'))
            self.elevatorOutOpen = 0
        

    
    def _DistributedCogdoInterior__playReservesJoining(self, ts, name, callback):
        index = 0
        for suit in self.joiningReserves:
            suit.reparentTo(render)
            suit.setPos(self.elevatorModelOut, Point3(ElevatorPoints[index][0], ElevatorPoints[index][1], ElevatorPoints[index][2]))
            index += 1
            suit.setH(180)
            suit.loop('neutral')
        
        if len(self.suits) == len(self.joiningReserves):
            camSequence = Sequence(Func(camera.wrtReparentTo, localAvatar), Func(camera.setPos, Point3(0, 5, 5)), Func(camera.headsUp, self.elevatorModelOut))
        else:
            camSequence = Sequence(Func(camera.wrtReparentTo, self.elevatorModelOut), Func(camera.setPos, Point3(0, -8, 2)), Func(camera.setHpr, Vec3(0, 10, 0)))
        track = Sequence(camSequence, Parallel(SoundInterval(self.openSfx), LerpPosInterval(self.leftDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], Point3(0, 0, 0), startPos = ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL), blendType = 'easeOut'), LerpPosInterval(self.rightDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], Point3(0, 0, 0), startPos = ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL), blendType = 'easeOut')), Wait(SUIT_HOLD_ELEVATOR_TIME), Func(camera.wrtReparentTo, render), Func(callback))
        track.start(ts)
        self.activeIntervals[name] = track

    
    def enterReservesJoining(self, ts = 0):
        self._DistributedCogdoInterior__playReservesJoining(ts, self.uniqueName('reserves-joining'), self._DistributedCogdoInterior__handleReserveJoinDone)

    
    def _DistributedCogdoInterior__handleReserveJoinDone(self):
        self.joiningReserves = []
        self.elevatorOutOpen = 1
        self.d_reserveJoinDone()

    
    def exitReservesJoining(self):
        self._DistributedCogdoInterior__finishInterval(self.uniqueName('reserves-joining'))

    
    def enterResting(self, ts = 0):
        self._showExitElevator()
        self._setAvPosFDC = FrameDelayedCall('setAvPos', self._setAvPosToExit)
        if self._wantBarrelRoom:
            self.barrelRoom.showBattleAreaLight(True)
        
        base.playMusic(self.waitMusic, looping = 1, volume = 0.69999999999999996)
        self._DistributedCogdoInterior__closeInElevator()
        self._haveEntranceElevator.set(False)
        self._stashEntranceElevator.set(False)

    
    def _setAvPosToExit(self):
        base.localAvatar.setPos(self.elevOut, 0, -10, 0)
        base.localAvatar.setHpr(self.elevOut, 0, 0, 0)
        base.cr.playGame.getPlace().fsm.request('walk')

    
    def exitResting(self):
        self._setAvPosFDC.destroy()
        self.waitMusic.stop()

    
    def enterReward(self, ts = 0):
        if self.isBossFloor(self.currentFloor):
            self.penthouseOutroTrack = self._DistributedCogdoInterior__outroPenthouse()
            self.penthouseOutroTrack.start(ts)
        else:
            self.exitCogdoBuilding()

    
    def exitReward(self):
        self.notify.debug('exitReward')
        if self.penthouseOutroTrack:
            self.penthouseOutroTrack.finish()
            DelayDelete.cleanupDelayDeletes(self.penthouseOutroTrack)
            self.penthouseOutroTrack = None
            if not self.penthouseOutroChatDoneTrack:
                self.notify.debug('exitReward: instanting outroPenthouseChatDone track')
                self._DistributedCogdoInterior__outroPenthouseChatDone()
            
            self.penthouseOutroChatDoneTrack.finish()
            self.penthouseOutroChatDoneTrack = None
        

    
    def enterFailed(self, ts = 0):
        self.exitCogdoBuilding()

    
    def exitFailed(self):
        self.notify.debug('exitFailed()')
        self.exitCogdoBuilding()

    
    def exitCogdoBuilding(self):
        if base.localAvatar.hp < 0:
            return None
        
        base.localAvatar.b_setParent(ToontownGlobals.SPHidden)
        request = {
            'loader': ZoneUtil.getBranchLoaderName(self.extZoneId),
            'where': ZoneUtil.getToonWhereName(self.extZoneId),
            'how': 'elevatorIn',
            'hoodId': ZoneUtil.getHoodId(self.extZoneId),
            'zoneId': self.extZoneId,
            'shardId': None,
            'avId': -1,
            'bldgDoId': self.distBldgDoId }
        messenger.send('DSIDoneEvent', [
            request])

    
    def displayBadges(self):
        numFloors = self.layout.getNumGameFloors()
        if numFloors > 5 or numFloors < 3:
            pass
        1
        self.notify.warning('Invalid floor number for display badges.')
        for player in range(len(self.toons)):
            goldBadge = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_crg_goldTrophy')
            goldBadge.setScale(1.2)
            goldNode = render.find('**/gold_0' + str(player + 1))
            goldBadge.reparentTo(goldNode)
            for floor in range(numFloors):
                silverBadge = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_crg_silverTrophy.bam')
                silverBadge.setScale(1.2)
                silverNode = render.find('**/silver_0' + str(floor * 4 + player + 1))
                silverBadge.reparentTo(silverNode)
            
        

    
    def _DistributedCogdoInterior__outroPenthouse(self):
        avatar = base.localAvatar
        trackName = '__outroPenthouse-%d' % avatar.doId
        track = Parallel(name = trackName)
        base.cr.playGame.getPlace().fsm.request('stopped')
        speech = TTLocalizer.CogdoExecutiveSuiteToonThankYou % self.SOSToonName
        track.append(Sequence(Func(camera.wrtReparentTo, localAvatar), Func(camera.setPos, 0, -9, 9), Func(camera.lookAt, Point3(5, 15, 0)), Parallel(self.cage.posInterval(0.75, self.cagePos[1], blendType = 'easeOut'), SoundInterval(self.cageLowerSfx, duration = 0.5)), Parallel(self.cageDoor.hprInterval(0.5, VBase3(0, 90, 0), blendType = 'easeOut'), Sequence(SoundInterval(self.cageDoorSfx), duration = 0)), Wait(0.25), Func(self.shopOwnerNpc.wrtReparentTo, render), Func(self.shopOwnerNpc.setScale, 1), Func(self.shopOwnerNpc.loop, 'walk'), Func(self.shopOwnerNpc.headsUp, Point3(0, 10, 0)), ParallelEndTogether(self.shopOwnerNpc.posInterval(1.5, Point3(0, 10, 0)), self.shopOwnerNpc.hprInterval(0.5, VBase3(180, 0, 0), blendType = 'easeInOut')), Func(self.shopOwnerNpc.setChatAbsolute, TTLocalizer.CagedToonYippee, CFSpeech), ActorInterval(self.shopOwnerNpc, 'jump'), Func(self.shopOwnerNpc.loop, 'neutral'), Func(self.shopOwnerNpc.headsUp, localAvatar), Func(self.shopOwnerNpc.setLocalPageChat, speech, 0), Func(camera.lookAt, self.shopOwnerNpc, Point3(0, 0, 2))))
        self.activeIntervals[trackName] = track
        self.accept('doneChatPage', self._DistributedCogdoInterior__outroPenthouseChatDone)
        return track

    
    def _DistributedCogdoInterior__outroPenthouseChatDone(self, elapsed = None):
        self.shopOwnerNpc.setChatAbsolute(TTLocalizer.CogdoExecutiveSuiteToonBye, CFSpeech)
        self.ignore('doneChatPage')
        track = Parallel(Sequence(ActorInterval(self.shopOwnerNpc, 'wave'), Func(self.shopOwnerNpc.loop, 'neutral')), Sequence(Wait(2.0), Func(self.exitCogdoBuilding), Func(base.camLens.setFov, ToontownGlobals.DefaultCameraFov)))
        track.start()
        self.penthouseOutroChatDoneTrack = track


