# File: t (Python 2.4)

from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
import Walk

class PublicWalk(Walk.Walk):
    notify = DirectNotifyGlobal.directNotify.newCategory('PublicWalk')
    
    def __init__(self, parentFSM, doneEvent):
        Walk.Walk.__init__(self, doneEvent)
        self.parentFSM = parentFSM

    
    def load(self):
        Walk.Walk.load(self)

    
    def unload(self):
        Walk.Walk.unload(self)
        del self.parentFSM

    
    def enter(self, slowWalk = 0):
        Walk.Walk.enter(self, slowWalk)
        base.localAvatar.book.showButton()
        self.accept(StickerBookHotkey, self._PublicWalk__handleStickerBookEntry)
        self.accept('enterStickerBook', self._PublicWalk__handleStickerBookEntry)
        self.accept(OptionsPageHotkey, self._PublicWalk__handleOptionsEntry)
        base.localAvatar.laffMeter.start()
        base.localAvatar.beginAllowPies()

    
    def exit(self):
        Walk.Walk.exit(self)
        base.localAvatar.book.hideButton()
        self.ignore(StickerBookHotkey)
        self.ignore('enterStickerBook')
        self.ignore(OptionsPageHotkey)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.endAllowPies()

    
    def _PublicWalk__handleStickerBookEntry(self):
        currentState = base.localAvatar.animFSM.getCurrentState().getName()
        if currentState == 'jumpAirborne':
            return None
        
        if base.localAvatar.book.isObscured():
            return None
        else:
            doneStatus = { }
            doneStatus['mode'] = 'StickerBook'
            messenger.send(self.doneEvent, [
                doneStatus])
            return None

    
    def _PublicWalk__handleOptionsEntry(self):
        currentState = base.localAvatar.animFSM.getCurrentState().getName()
        if currentState == 'jumpAirborne':
            return None
        
        if base.localAvatar.book.isObscured():
            return None
        else:
            doneStatus = { }
            doneStatus['mode'] = 'Options'
            messenger.send(self.doneEvent, [
                doneStatus])
            return None


