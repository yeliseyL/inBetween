""" inBetween - set of animation scripts for SideFX Houdini

    DESCRIPTION:
    This plugin combines multiple features for traditional keyframe animation,
    such as automated breakdown pose creation, custom static ghosting, quick selection sets,
    instant reference import and more.
  	
    AUTHOR:
  	Elisey Lobanov - http://www.eliseylobanov.com

    COPYRIGHT:
  	Copyright 2019 Elisey Lobanov - All Rights Reserved
"""

import hou
import math
import os
import sys
import toolutils
import webbrowser

from hutil.Qt import QtCore, QtGui, QtWidgets

class BreakdownKeysInterface(QtWidgets.QWidget):
    def __init__(self, paneTab):
        """Define all the elements of the user interface."""
        QtWidgets.QWidget.__init__(self)
        self.setMouseTracking(True)        
        self.factor = 100
        self.mouseX = 0
        self.mouseY = 0
        hou.playbar.addEventCallback(self.outputPlaybarEvent)
        
        self.icons_path = hou.findDirectory('python_panels')+'/InBetween_icons/'

        self.nameLabel = QtWidgets.QLabel(self)
        self.nameLabel.setText('inBetween 1.0')
        self.nameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.nameLabel.mousePressEvent = self.help
        self.nameLabelLayout = QtWidgets.QHBoxLayout()
        self.nameLabelLayout.addWidget(self.nameLabel)
                   
        self.valueSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.valueSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.valueSlider.setTickInterval(1)
        self.valueSlider.setValue(0)
        self.valueSlider.setStyleSheet("QSlider:handle {width: 14px;}")
        self.valueSlider.setMinimum(-100)
        self.valueSlider.setMaximum(100)
        self.valueSlider.setSingleStep(1)
        self.valueSlider.setToolTip('Creates a breakdown pose for the selected objects.')  

        invisible_btn_stylesheet = "QPushButton {border: transparent;background: transparent;height: 48px;width: 120px;} QPushButton:hover {background-color: rgb(0,0,0, 0);height: 48px;width: 120px;}"
                
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.sizePolicy.setHeightForWidth(True)

        self.zeroBtn = QtWidgets.QPushButton(self)
        self.zeroBtn.setMaximumHeight(30)
        self.zeroBtn.setSizePolicy(self.sizePolicy)
        self.zeroBtn.clicked.connect(self.zeroBtnAction)                      
        self.zeroBtn.setStyleSheet(invisible_btn_stylesheet)
           
        self.minStepBtn = QtWidgets.QPushButton(self)
        self.minStepBtn.setMaximumHeight(30)
        self.minStepBtn.setSizePolicy(self.sizePolicy)
        self.minStepBtn.clicked.connect(self.minStepBtnAction)        
        self.minStepBtn.setStyleSheet(invisible_btn_stylesheet)
        
        self.plusStepBtn = QtWidgets.QPushButton(self)
        self.plusStepBtn.setMaximumHeight(30)
        self.plusStepBtn.setSizePolicy(self.sizePolicy)
        self.plusStepBtn.clicked.connect(self.plusStepBtnAction)             
        self.plusStepBtn.setStyleSheet(invisible_btn_stylesheet)
        
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addWidget(self.minStepBtn, 1)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.zeroBtn, 1)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.plusStepBtn, 1)
        
        self.makeGhostBtn = QtWidgets.QPushButton(self)        
        self.makeGhostBtn.setMinimumHeight(30)
        self.makeGhostBtn.setSizePolicy(self.sizePolicy)
        self.makeGhostBtn.setIcon(QtGui.QPixmap(self.icons_path + 'ghost.png'))        
        self.makeGhostBtn.clicked.connect(self.manuallyCreateGhost)
        self.makeGhostBtn.setToolTip('Makes a new ghost.')  
        self.delGhostBtn = QtWidgets.QPushButton(self)
        self.delGhostBtn.setMinimumHeight(30)
        self.delGhostBtn.setSizePolicy(self.sizePolicy)
        self.delGhostBtn.setIcon(QtGui.QPixmap(self.icons_path + 'deghost.png')) 
        self.delGhostBtn.clicked.connect(self.deleteCurrentGhost)
        self.delGhostBtn.setToolTip('Deletes current ghost.')  
            
        self.copyToTwosBtn = QtWidgets.QPushButton(self)
        self.copyToTwosBtn.setMinimumHeight(30)
        self.copyToTwosBtn.setSizePolicy(self.sizePolicy)
        self.copyToTwosBtn.setIcon(QtGui.QPixmap(self.icons_path + 'plus_two.png')) 
        self.copyToTwosBtn.clicked.connect(self.copyToTwos)
        self.copyToTwosBtn.setToolTip('Copies current pose +2.')  
        self.copyToFoursBtn = QtWidgets.QPushButton(self)
        self.copyToFoursBtn.setMinimumHeight(30)
        self.copyToFoursBtn.setSizePolicy(self.sizePolicy)
        self.copyToFoursBtn.setIcon(QtGui.QPixmap(self.icons_path + 'plus_four.png'))
        self.copyToFoursBtn.clicked.connect(self.copyToFours)
        self.copyToFoursBtn.setToolTip('Copies current pose +4.')  
        
        self.ghostLabel = QtWidgets.QLabel(self)
        self.ghostLabel.setText('Ghosting')
        self.ghostLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.copyLabel = QtWidgets.QLabel(self)
        self.copyLabel.setText('Copy Pose')
        self.copyLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.copyLabelLayout = QtWidgets.QHBoxLayout()
        self.copyLabelLayout.addWidget(self.ghostLabel)
        self.copyLabelLayout.addWidget(self.copyLabel)
        self.copyLabelLayout.setSpacing(20)
        
        self.ghostColorLabel = QtWidgets.QLabel(self)
        self.ghostColorLabel.setStyleSheet("QLabel {background-color: #E57200;}")
        self.ghostColorLabel.setMinimumHeight(30)
        self.ghostColorLabel.setSizePolicy(self.sizePolicy)
        self.ghostColorLabel.mousePressEvent = self.colorDialogCall
        self.ghostColorLabel.setToolTip('Sets a color for the current ghost.') 
        
        self.ghostSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.ghostSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.ghostSlider.setStyleSheet("QSlider:handle {width: 14px;}")
        self.ghostSlider.setTickInterval(1)
        self.ghostSlider.setValue(0)
        self.ghostSlider.setMinimum(100)
        self.ghostSlider.setMaximum(200)
        self.ghostSlider.setSingleStep(1)
        self.ghostSlider.setSizePolicy(self.sizePolicy)
        self.ghostSlider.setToolTip('Sets a visibility for the current ghost.')
        
        self.setRefBtn = QtWidgets.QPushButton(self)
        self.setRefBtn.setMinimumHeight(30)
        self.setRefBtn.setSizePolicy(self.sizePolicy)
        self.setRefBtn.setIcon(QtGui.QPixmap(self.icons_path + 'ref.png'))
        self.setRefBtn.clicked.connect(self.addReferencePlane)
        self.setRefBtn.setToolTip('Creates a reference plane.') 

        self.selectionSet = QtWidgets.QPushButton(self)
        self.selectionSet.setMinimumHeight(30)
        self.selectionSet.setSizePolicy(self.sizePolicy)
        self.selectionSet.setIcon(QtGui.QPixmap(self.icons_path + 'selection.png'))
        self.selectionSet.clicked.connect(self.createNewSelectionSet)
        self.selectionSet.setToolTip('Creates selection set.')                          
        
        self.grid_left = QtWidgets.QGridLayout()
        self.grid_left.addWidget(self.delGhostBtn, 0, 0)
        self.grid_left.addWidget(self.makeGhostBtn, 0, 1)
        self.grid_left.addWidget(self.ghostColorLabel, 1, 0)
        self.grid_left.addWidget(self.ghostSlider, 1, 1)
        self.grid_left.setSpacing(8)

        self.grid_right = QtWidgets.QGridLayout()
        self.grid_right.addWidget(self.copyToTwosBtn, 0, 0)
        self.grid_right.addWidget(self.copyToFoursBtn, 0, 1)
        self.grid_right.addWidget(self.setRefBtn, 1, 0)
        self.grid_right.addWidget(self.selectionSet, 1, 1)
        self.grid_right.setSpacing(8)

        self.bottomLayout = QtWidgets.QHBoxLayout()
        self.bottomLayout.addLayout(self.grid_left)
        self.bottomLayout.addLayout(self.grid_right)
        self.bottomLayout.setSpacing(20)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.nameLabelLayout)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.valueSlider)
        self.layout.addLayout(self.copyLabelLayout)
        self.layout.addLayout(self.bottomLayout)
        self.layout.setSpacing(8)
        self.valueSlider.valueChanged.connect(self.sliderVal)
        self.valueSlider.sliderMoved.connect(self.repaintValue)
        self.valueSlider.sliderReleased.connect(self.setBetweenKey)
        self.ghostSlider.valueChanged.connect(self.ghostWidth)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
    def repaintValue(self):
        """Repaint interface on slider move."""
        self.repaint()
    
    def sliderVal(self):
        """Get main slider value."""        
        return self.valueSlider.value()
              
    def mouseMoveEvent(self, event): 
        """Repaint interface on mouse move."""        
        self.repaint()
        
    def resizeEvent(self, event):
        """Scale icons and text according to window resize."""
        width = self.delGhostBtn.width()
        height = self.setRefBtn.height()
        button_stylesheet = "QPushButton {border: transparent;background-color: #484848;icon-size: "+str(height-3)+"px;font: "+str(width/10+0.1)+"pt} QPushButton:hover {background-color: #545454;} QPushButton:pressed {background-color: #5675A7;}"
        self.delGhostBtn.setStyleSheet(button_stylesheet)
        self.makeGhostBtn.setStyleSheet(button_stylesheet)
        self.copyToTwosBtn.setStyleSheet(button_stylesheet)
        self.copyToFoursBtn.setStyleSheet(button_stylesheet)
        self.setRefBtn.setStyleSheet(button_stylesheet) 
        self.selectionSet.setStyleSheet(button_stylesheet)      
        self.copyLabel.setStyleSheet("QLabel  {font: "+str(width/14+0.1)+"pt}")
        self.ghostLabel.setStyleSheet("QLabel  {font: "+str(width/14+0.1)+"pt}")
        self.nameLabel.setStyleSheet("QLabel  {font: 10pt}")
        
    def zeroBtnAction(self):
        """Moves slider incrementally to zero."""        
        value = self.valueSlider.value()
        if value > 50:
            self.valueSlider.setValue(50)
        elif value <= 50 and value >= -50:
            self.valueSlider.setValue(0)
        else:
            self.valueSlider.setValue(-50)
        self.setBetweenKey()
        self.repaint()
                 
    def minStepBtnAction(self):
        """Moves slider incrementally to minimum."""   
        value = self.valueSlider.value()
        if value > 50:
            self.valueSlider.setValue(50)
        elif value <= 50 and value > 0:
            self.valueSlider.setValue(0)
        elif value <= 0 and value > -50:
            self.valueSlider.setValue(-50)
        else:
            self.valueSlider.setValue(-100)
        self.setBetweenKey()
        self.repaint()
            
    def plusStepBtnAction(self):
        """Moves slider incrementally to maximum."""  
        value = self.valueSlider.value()
        if value >= 50:
            self.valueSlider.setValue(100)
        elif value < 50 and value >= 0:
            self.valueSlider.setValue(50)
        elif value < 0 and value >= -50:
            self.valueSlider.setValue(0)
        else:
            self.valueSlider.setValue(-50)
        self.setBetweenKey()
        self.repaint()
        
    def contextMenuEvent(self, event):
        """Define context menu content.""" 
        contextMenu = QtWidgets.QMenu(self)
        steppedAct = contextMenu.addAction("Convert to Stepped")
        linearAct = contextMenu.addAction("Convert to Linear")
        splinesAct = contextMenu.addAction("Convert to Bezier")
        contextMenu.addSeparator()
        cleanCurves = contextMenu.addAction("Clean Curves")
        contextMenu.addSeparator()
        killAllGhosts = contextMenu.addAction("Kill All Ghosts")
        action = contextMenu.exec_(QtGui.QCursor.pos())
        
        if action == steppedAct:
            type = "constant"
            self.convertAllKeys(type)
            
        if action == linearAct:
            type = "linear"
            self.convertAllKeys(type)
            
        if action == splinesAct:
            type = "bezier"
            self.convertAllKeys(type)
            
        if action == cleanCurves:         
            self.cleanCurves()
            
        if action == killAllGhosts:         
            self.killAllGhosts()
            
    def cleanCurves(self):
        """Delete all the redundant keys on all animated parameters of all selected objects.""" 
        nodes = hou.selectedNodes()
        with hou.undos.group("Clean Curves"):
            self.convertAllKeys("ease")        
            for node in nodes:
                for parm in node.parms():
                    parm = parm.getReferencedParm()
                    if len(parm.keyframes()) > 0 and type(parm.eval()) == float and parm.isLocked() == False:                 
                        for key in parm.keyframes()[1:-1]:                    
                            if key.value() == parm.evalAsFloatAtFrame(key.frame()+1) and key.value() == parm.evalAsFloatAtFrame(key.frame()-1):
                                parm.deleteKeyframeAtFrame(key.frame())
            self.convertAllKeys("bezier")
            
    def killAllGhosts(self):
        """Delete hidden obj containing all ghosts.""" 
        if hou.node("/obj/InBetween_ghost_folder"):
            node = hou.node("/obj/InBetween_ghost_folder")
            node.destroy()
            
    def pickGhostColor(self, color, alpha):
        """Change the color of the current ghost.

        INPUT:
        color -- color object from Color Editor
        alpha -- alpha from Color Editor
        """
        new_color = QtGui.QColor.fromRgbF(color.rgb()[0], color.rgb()[1], color.rgb()[2])
        self.ghostColorLabel.setStyleSheet("QLabel {background-color: "+new_color.name()+";}")
        if hou.node("/obj/InBetween_ghost_folder/ghost_shaders/"):
            current_frame = hou.frame()
            ghost_mat_folder = hou.node("/obj/InBetween_ghost_folder/ghost_shaders/")
            for shader in ghost_mat_folder.children():
                shader_frame = shader.name().split("_")[-1]
                if shader_frame == str(current_frame):
                    shader.setParms({"ogl_specx": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).redF(), "ogl_specy": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).greenF(), "ogl_specz": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).blueF()})
  
    def colorDialogCall(self, event):
        """Call Houdini Color Editor.""" 
        init_color = hou.Color(self.ghostColorLabel.palette().color(QtGui.QPalette.Base).redF(), self.ghostColorLabel.palette().color(QtGui.QPalette.Base).greenF(), self.ghostColorLabel.palette().color(QtGui.QPalette.Base).blueF())
        return hou.ui.openColorEditor(self.pickGhostColor, initial_color=init_color)
        
    def outputPlaybarEvent(self, event_type, frame):
        """Change the color of UI color label in accordance with the ghost in current frame.""" 
        ghost_mat_folder = hou.node("/obj/InBetween_ghost_folder/ghost_shaders/")
        if ghost_mat_folder:
            for shader in ghost_mat_folder.children():
                shader_frame = shader.name().split("_")[-1]
                if shader_frame == str(float(frame)):
                    ghost_color = QtGui.QColor.fromRgbF(shader.parm("ogl_specx").eval(), shader.parm("ogl_specy").eval(), shader.parm("ogl_specz").eval())
                    self.ghostColorLabel.setStyleSheet("QLabel {background-color: " + ghost_color.name() + ";}")
        
    def ghostWidth(self):
        """Change outline width of the current ghost.""" 
        ghost_mat_folder = hou.node("/obj/InBetween_ghost_folder/ghost_shaders/")
        if ghost_mat_folder:
            for shader in ghost_mat_folder.children():
                shader.parm("ogl_ior").set(float(self.ghostSlider.value())/100)
                                  
    def getSeqExpression(self, path):
        """Generate expression for reference plane material.
        
        INPUTS:
        path -- given file path string

        OUTPUTS:
        seq_expression -- generated sequence expression
        clean_path -- path for image resolution method
        """     
        start_path = path[:-4]
        path_split = path.split('.')
        extension = path_split[-1]
        frame_exp = ''
        zeroes = ''
        if '$F' in start_path:
            zeroes = start_path.split('$F')[-1]
            frame_exp = '$F' + zeroes
            if zeroes  == "":
                seq_expression = start_path.split('$F')[-2] + "`" + frame_exp + """-chs("../../frame_offset")`""" + "." + extension
            else:
                seq_expression = start_path.split('$F')[-2] + "`padzero(" + zeroes + ", " + "$F" + """-chs("../../frame_offset"))`""" + "." + extension
            clean_path = start_path.split('$F')[-2] + hou.expandString(frame_exp) + "." + extension
        else:
            seq_expression = path
            clean_path = path
        return seq_expression, clean_path

    def createReferencePlane(self, width, height, path):
        """Create reference plane object from a given file sequence and orient it to a current view.
        
        INPUTS:
        width -- image width
        height -- image height
        path -- given file sequence path string
        """  
        with hou.undos.group("Create Reference Plane"):   
            viewer = toolutils.sceneViewer()
            a = viewer.curViewport().viewTransform().extractRotates()
            b = viewer.curViewport().viewTransform().extractTranslates()
            
            temp_null = hou.node('obj/').createNode('null', 'IB_Temp_Null')
            temp_null.setParms({'tx': b[0], 'ty': b[1], 'tz': b[2], 'rx': a[0], 'ry': a[1], 'rz': a[2]})
            
            geo = hou.node('obj/').createNode('geo', 'IB_Reference_Plane')
            geo_parm_group = geo.parmTemplateGroup()
            geo_parm_folder = hou.FolderParmTemplate("folder", "Controls")
            geo_parm_folder.addParmTemplate(hou.IntParmTemplate("frame_offset", "Frame Offset", 1, min=-100, max=100))
            geo_parm_group.append(geo_parm_folder)
            geo.setParmTemplateGroup(geo_parm_group)
            
            ref = geo.createNode('shopnet', 'Reference_Sequence')
            ref.moveToGoodPosition()
            ref_mat = ref.createNode('vopmaterial', 'Reference_Mat')    
            parm_group = ref_mat.parmTemplateGroup()
            parm_folder = hou.FolderParmTemplate("folder", "OpenGL")
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_diff", "Diffuse", 3))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_emit", "Emission", 3))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_emit_intensity", "Emission Intensity", 1))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_rough", "Roughness", 1))
            parm_folder.addParmTemplate(hou.ToggleParmTemplate("ogl_use_emit", "Enable Emission"))
            parm_folder.addParmTemplate(hou.ToggleParmTemplate("ogl_use_emissionmap", "Use Emission Map"))
            parm_folder.addParmTemplate(hou.StringParmTemplate("ogl_emissionmap", "Emission Map", 1))
            parm_group.append(parm_folder)
            ref_mat.setParmTemplateGroup(parm_group)
            ref_mat.setParms({"ogl_diffx": 0, "ogl_diffy": 0, "ogl_diffz": 0, "ogl_emitx": 1, "ogl_emity": 1, "ogl_emitz": 1, "ogl_emit_intensity": 1, "ogl_rough": 0, "ogl_use_emit": 1, "ogl_use_emissionmap": 1, "ogl_emissionmap": path})
            
            grid = geo.createNode('grid')
            grid.setParms({'orient': 0, 'sizex': float(width)/100, 'sizey': float(height)/100, 'rows': 2, 'cols': 2})
            uv_set = geo.createNode('uvproject')
            uv_set.setInput(0, grid)
            uv_set.parm('inittype').set(0)
            uv_set.parm('initbbox').pressButton()
            mat = geo.createNode('material')
            mat.setInput(0, uv_set)
            mat.parm('shop_materialpath1').set('../Reference_Sequence/Reference_Mat')    
            mat.setDisplayFlag(1)
            mat.setRenderFlag(1) 
            geo.layoutChildren()
            
            geo.setInput(0, temp_null)
            geo.parm('tz').set(-50)
            geo.parm('keeppos').set(1)
            geo.setInput(0, None)
            temp_null.destroy() 

    def hipConvert(self, path):
        """If true, convert HIP variable inside given path to its value and return the result

        INPUT:
        path -- path to a file
        """
        new_path = ""
        hip_value = hou.expandString('$HIP')
        if path[:4] == "$HIP": 
            new_path = hip_value + path[4:]
            return new_path  
        return path 
            
    def addReferencePlane(self):
        """Call Select File dialogue and create a reference plane from the selected sequence.""" 
        path = hou.ui.selectFile(title='Select Reference', collapse_sequences=True, file_type=hou.fileType.Image)
        if path:
            path = self.hipConvert(path)       
            ref_expr, clean_path = self.getSeqExpression(path)
            file_width = hou.imageResolution(clean_path)[0]
            file_height = hou.imageResolution(clean_path)[1]
            self.createReferencePlane(file_width, file_height, ref_expr)
        
    def help(self, event):
        """Launch the help page with the default browser.""" 
        webbrowser.open('http://www.google.com')
               
    def paintEvent(self, event):
        """Paint main slider UI elements.""" 
        pos = self.valueSlider.pos()
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        font = QtGui.QFont()
        font.setPixelSize(self.width()/30)
        painter.setFont(font)
        
        color = QtGui.QColor(self.factor*0.5, self.factor*0.5, self.factor * 0.5)
        painter.fillRect(0, 0, self.width(), self.height(), color)
        value_color = QtGui.QColor(self.factor*1.3, self.factor*0.8, self.factor * 0.1)
        painter.setBrush(value_color)
        painter.setPen(value_color)
        painter.drawRect(self.width()/2, pos.y()+4, (self.width()/2 - 12) * self.sliderVal()/100, 4)
        painter.setPen(QtGui.QColor(self.factor * 1.5, self.factor * 1.5, self.factor * 1.5))
        if self.sliderVal() > 0:
            pose_favor_ratio = str(abs(self.sliderVal())) + "%" 
            painter.drawText(QtCore.QPoint(self.width()/2+self.width()/16, pos.y()-10), "  > > >" )
        elif self.sliderVal() < 0:
            pose_favor_ratio = str(abs(self.sliderVal())) + "%"
            painter.drawText(QtCore.QPoint(self.width()/2-self.width()/13, pos.y()-10), "< < <  " )
        else:
            pose_favor_ratio = str(abs(self.sliderVal())) + "%" 
                
        painter.drawText(self.width()/30+12, pos.y()-10, "Prev Pose")
        painter.drawText(QtCore.QPoint(self.width()/2, pos.y()-10), pose_favor_ratio)
        painter.drawText(self.width()*0.82-10, pos.y()-10, "Next Pose")      
        value_color = QtGui.QColor(self.factor*0.1, self.factor*0.1, self.factor * 0.1)
        painter.setBrush(value_color)
        painter.setPen(value_color)
        painter.drawRect(10, pos.y()-10, self.width()/40, -self.width()/40)
        painter.drawRect(self.width()-10-self.width()/40, pos.y()-10, self.width()/40, -self.width()/40)
        if self.sliderVal() > 0:
            value_color = QtGui.QColor(self.factor*1.3, self.factor*0.8, self.factor*0.1, 255*abs(float(self.sliderVal())/100))
            painter.setBrush(value_color)
            painter.setPen(value_color)
            painter.drawRect(self.width()-10-self.width()/40, pos.y()-10, self.width()/40, -self.width()/40)
        if self.sliderVal() < 0:
            value_color = QtGui.QColor(self.factor*1.3, self.factor*0.8, self.factor*0.1, 255*abs(float(self.sliderVal())/100))
            painter.setBrush(value_color)
            painter.setPen(value_color)
            painter.drawRect(10, pos.y()-10, self.width()/40, -self.width()/40)
    
    def deleteOldKeyframe(self, param):
        """Delete old key at current frame.
        INPUTS:
        param -- parameter which keys must be deleted
        """ 
        currentFrame = hou.frame()
        for key in param.keyframes(): #check all keys at given parm
            if key.frame() == currentFrame: #if its frame is the same as current 
                param.deleteKeyframeAtFrame(currentFrame)
    
    def convertKeys(self, key, param, exp_type):
        """Convert keyframe type.
        
        INPUTS:
        key -- current key
        param -- parameter to set a new keyframe on
        type -- new keyframe type

        OUTPUTS:
        newKey -- converted key
        """ 
        newKey = hou.Keyframe() #instantiate new keyframe object
        newKey.setFrame(key.frame()) #set frame for the new key
        newKey.setValue(key.value())
        newKey.setExpression(exp_type + "()") #set key interpolation 
        newKey.setSlopeAuto(True)
        newKey.setInSlopeAuto(True)
        param = param.getReferencedParm()         
        param.setKeyframe(newKey)
        return newKey
    
    def getValueFromConstant(self, param):
        """Get new frame value after conversion to linear and convert back to constant type.
        
        INPUTS:
        param -- current param

        OUTPUTS:
        value -- new value
        """ 
        currentFrame = hou.frame()
        prevKey = param.keyframesBefore(currentFrame)[-1] 
        nextKey = param.keyframesAfter(currentFrame)[0]
        exp_type = "linear"
        self.convertKeys(prevKey, param, exp_type)
        self.convertKeys(nextKey, param, exp_type)
        value = param.eval()
        exp_type = "constant"
        self.convertKeys(prevKey, param, exp_type)
        self.convertKeys(nextKey, param, exp_type)
        return value
        
    def calculateValue(self, param):
        """Calculate the new key value based on the nieghbour key values and slider value coef.
        
        INPUTS:
        param -- current param

        OUTPUTS:
        calculatedValue -- new value
        """ 
        currentFrame = hou.frame()
        self.deleteOldKeyframe(param)
        coef = float(self.valueSlider.value())/100 #calculate a coefficient from a slider value
        prevKey = param.keyframesBefore(currentFrame)[-1] #get value from the previous key
        nextKey = param.keyframesAfter(currentFrame)[0] #get value from the next key
        
        if prevKey.expression() == "constant()" or nextKey.expression() == "constant()": #if keyframe type is constant
            calculatedValue = self.getValueFromConstant(param) #convert nieghbours to linear and get current parameter value
        else:    
            calculatedValue = param.eval() #set the new key value to current parameter value
        
        if coef > 0:
            calculatedValue += (nextKey.value() - calculatedValue) * abs(coef)
        elif coef < 0:
            calculatedValue -= (calculatedValue - prevKey.value()) * abs(coef)
        else:
            calculatedValue = param.eval()
        
        return calculatedValue
            
    def getBetweenKeyValue(self, param):
        """Calculate a value for the new key.
        
        INPUTS:
        param -- current param

        OUTPUTS:
        betweenKeyValue -- new value
        """ 
        currentFrame = hou.frame()
        keysBefore = param.keyframesBefore(currentFrame) #get previous keys
        keysAfter = param.keyframesAfter(currentFrame) #get next keys
        
        #check if there's only one nieghbour key or no keys
        if keysBefore == () or keysAfter == ():
            betweenKeyValue = param.eval()
            
        #check if there's a key at current frame and no neighbour
        elif (keysBefore[-1].frame() == currentFrame and len(keysBefore) == 1) or (keysAfter[0].frame() == currentFrame and len(keysAfter) == 1):
            betweenKeyValue = param.eval()
        else:
            betweenKeyValue = self.calculateValue(param)
        
        return betweenKeyValue
        
    def setBetweenKey(self):
        """Set a new key with the new value."""
        controls = hou.selectedNodes() #initiate currently selected objects
        with hou.undos.group("Set Between Key"): #record changes as single action for one undo
            for control in controls: #iterate between selected objects
                for parm in control.parms(): #for every object iterate between its parameters
                    parm = parm.getReferencedParm()
                    if len(parm.keyframes()) > 0 and type(parm.eval()) == float: #if parameter is animated and its type is float
                        currentFrame = hou.frame() #get current frame number
                        key = hou.Keyframe() #instantiate new keyframe object
                        key.setFrame(currentFrame) #set frame for the new key
                        key.setValue(self.getBetweenKeyValue(parm)) #set value for the new key
                        key.setSlopeAuto(True)
                        key.setInSlopeAuto(True)
                        parm.setKeyframe(key) #set the new key on timeline

    def convertAllKeys(self, exp_type):
        """Convert all keys on all parameters to a given type.
        
        INPUTS:
        type -- new keyframe type
        """ 
        controls = hou.selectedNodes() #initiate currently selected objects
        with hou.undos.group("Convert Keys"): #record changes as single action for one undo
            for control in controls: #iterate between selected objects
                for parm in control.parms(): #for every object iterate between its parameters
                    parm = parm.getReferencedParm() 
                    if len(parm.keyframes()) > 0 and type(parm.eval()) == float and parm.isLocked() == False:               
                        for key in parm.keyframes():
                            self.convertKeys(key, parm, exp_type)
                                       
    def copyKeyframe(self, frame_step):
        """Copy all current keyframes on all selected objects to a specified frame.
        
        INPUTS:
        frame_step -- frame interval
        """
        current_frame = hou.frame()
        nodes = hou.selectedNodes()
        with hou.undos.group("Copy Keys"):
            for node in nodes:
                for parm in node.parms():
                    parm = parm.getReferencedParm()
                    if parm.keyframesBefore(current_frame) != () and len(parm.keyframes()) > 0 and type(parm.eval()) == float and parm.isLocked() == False:
                        new_key = hou.Keyframe()
                        new_key.setValue(parm.eval())
                        new_key.setSlopeAuto(1)
                        new_key.setFrame(current_frame + float(frame_step))
                        parm.setKeyframe(new_key)
                    else:
                        pass
            hou.setFrame(current_frame + frame_step)
        
    def copyToTwos(self):
        """Copy all current keyframes on all selected objects to a second frame after the current."""        
        self.copyKeyframe(2)
        
    def copyToFours(self):
        """Copy all current keyframes on all selected objects to a fourth frame after the current.""" 
        self.copyKeyframe(4)
    
    def ghostShaderCreate(self, ghost_mat_folder, ghost_name):
        """Create a shader for a new ghost.
        
        INPUTS:
        ghost_mat_folder -- ghost shader network folder
        ghost_name -- object name from which a new ghost is created

        OUTPUTS:
        ghost_shader -- new ghost shader node
        """ 
        with hou.undos.group("Create Ghost Shader"):
            current_frame = hou.frame()
            ghost_shader = ghost_mat_folder.createNode('vopmaterial', node_name=ghost_name+"_ghost_mat"+'_frame_'+str(current_frame))
            parm_group = ghost_shader.parmTemplateGroup()
            parm_folder = hou.FolderParmTemplate("folder", "OpenGL")
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_spec", "Specular", 3))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_transparency", "Transparency", 1))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_ior", "IOR", 1))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_spec_intensity", "Intensity", 1))
            parm_folder.addParmTemplate(hou.FloatParmTemplate("ogl_rough", "Roughness", 1))
            parm_group.append(parm_folder)
            ghost_shader.setParmTemplateGroup(parm_group)
            ghost_shader.setParms({"ogl_specx": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).redF(), "ogl_specy": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).greenF(), "ogl_specz": self.ghostColorLabel.palette().color(QtGui.QPalette.Base).blueF(),"ogl_transparency": 1, "ogl_ior": 1.06, "ogl_spec_intensity": 5, "ogl_rough": 0}) 
            ghost_shader.moveToGoodPosition()
            return ghost_shader

    def mergedNodes(self, ghost):
        """Return a list of all displayed child nodes in a given object.

        INPUTS:
        ghost -- selected object

        OUTPUTS:
        mergedNodes -- list of all displayed child nodes
        """
        mergedNodes = []
        if ghost.type().name() == 'geo':
            for node in ghost.children():      
                if node.isDisplayFlagSet() == True: 
                    mergedNodes.append(node)
        else:
            for node in ghost.children():      
                if node.type().name() == 'geo': 
                    mergedNodes.append(node)
        return mergedNodes
       
    def createGhost(self, ghost_mat_folder, ghost_geo_folder, ghosts):
        """Creates a new ghost in the ghost folder.

        INPUTS:
        ghosts -- selected objects
        ghost_mat_folder -- ghost shader network folder
        ghost_geo_folder -- ghost folder
        """
        with hou.undos.group("Create Ghost Func"): 
            current_frame = hou.frame()
            for ghost in ghosts:        
                ghost_name = ghost.name()
                ghosts_parts_merge = ghost_geo_folder.createNode('merge', node_name=ghost_name+'_parts_merge'+'_frame_'+str(current_frame))
                for node in self.mergedNodes(ghost):
                    ghost_merge = ghost_geo_folder.createNode('object_merge', node_name=node.name()+'_ghost'+'_frame_'+str(current_frame))
                    ghost_merge.parm("objpath1").set(node.path())
                    ghost_merge.parm("xformtype").set(1)
                    ghost_merge.setHardLocked(1)
                    ghosts_parts_merge.setNextInput(ghost_merge)
                ghost_convert = ghost_geo_folder.createNode('convert', node_name=ghost_name+'_convert'+'_frame_'+str(current_frame))
                ghost_convert.setInput(0, ghosts_parts_merge)
                ghost_clean = ghost_geo_folder.createNode('delete', node_name=ghost_name+'_clean'+'_frame_'+str(current_frame))
                ghost_clean.setInput(0, ghost_convert)
                ghost_clean.setParms({"negate": 1, "geotype": 17, "pattern": "*"})
                ghost_frame = ghost_geo_folder.createNode('timeshift', node_name=ghost_name+'_frame'+'_frame_'+str(current_frame))
                ghost_frame.setInput(0, ghost_clean)
                ghost_frame.parm("frame").deleteAllKeyframes()
                ghost_frame.parm("frame").set(current_frame)
                ghost_shader = self.ghostShaderCreate(ghost_mat_folder, ghost_name)
                ghost_material = ghost_geo_folder.createNode('material', node_name=ghost_name+'_material'+'_frame_'+str(current_frame))
                ghost_material.setInput(0, ghost_frame)
                ghost_material.parm("shop_materialpath1").set("../ghost_shaders/"+ghost_shader.name())
                if not hou.node("/obj/InBetween_ghost_folder/ghosts_merge"):
                    ghosts_merge = ghost_geo_folder.createNode('merge', node_name='ghosts_merge')
                    ghosts_merge.setInput(0, ghost_material)
                    ghost_pack = ghost_geo_folder.createNode('pack', node_name='ghosts_pack')
                    ghost_pack.setInput(0, ghosts_merge)
                    ghost_out = ghost_geo_folder.createNode('null', node_name='OUT_ghost')
                    ghost_out.setInput(0, ghost_pack)
                    ghost_out.setDisplayFlag(1)
                    ghost_out.setRenderFlag(1)
                else:
                    for child in ghost_geo_folder.children():
                        if child.name() == "ghosts_merge":
                            ghosts_merge = child
                            ghosts_merge.setNextInput(ghost_material)
                ghost_geo_folder.layoutChildren()
                
    def deleteExistingGhostAtFrame(self, ghost_geo_folder, ghost_mat_folder, ghosts):
        """Deletes a ghost at the current frame.

        INPUTS:
        ghosts -- selected objects
        ghost_mat_folder -- ghost shader network folder
        ghost_geo_folder -- ghost folder
        """
        with hou.undos.group("Delete Ghost"):  
            current_frame = hou.frame()
            for ghost in ghosts:
                ghost_name = ghost.name()
                existing_ghost_mat = hou.node('/obj/InBetween_ghost_folder/ghost_shaders/' + ghost_name + '_ghost_mat'+'_frame_'+str(current_frame))
                if existing_ghost_mat:
                    for node in ghost_geo_folder.glob(ghost_name+"*"+'_frame_'+str(current_frame)):
                        node.destroy()
                    for mat in ghost_mat_folder.glob(ghost_name + '_ghost_mat'+'_frame_'+str(current_frame)):
                        mat.destroy()
                
    def deleteCurrentGhost(self):
        """Deletes a ghost at the current frame or all the ghosts."""
        ghosts = hou.selectedNodes()
        if ghosts != ():
            if hou.node("/obj/InBetween_ghost_folder"):                                
                ghost_geo_folder = hou.node("/obj/InBetween_ghost_folder")
                ghost_mat_folder = hou.node("/obj/InBetween_ghost_folder/ghost_shaders/")
                if len(ghost_mat_folder.children()) == 1:
                    self.killAllGhosts()
                else:
                    self.deleteExistingGhostAtFrame(ghost_geo_folder, ghost_mat_folder, ghosts)
    
    def manuallyCreateGhost(self): 
        """Create a ghost at the current frame for a selected objects. If it already exists, delete it and create a new one."""       
        ghosts = hou.selectedNodes()
        if ghosts != ():
            if hou.node("/obj/InBetween_ghost_folder"):
                for node in hou.node("/obj").allItems():
                    if node.name() == "InBetween_ghost_folder":
                        ghost_geo_folder = node
                        ghost_mat_folder = hou.node("/obj/InBetween_ghost_folder/ghost_shaders/")
                        self.deleteExistingGhostAtFrame(ghost_geo_folder, ghost_mat_folder, ghosts)
                        self.createGhost(ghost_mat_folder, ghost_geo_folder, ghosts)                    
            else: 
                with hou.undos.group("Create Ghost"):   
                    ghost_geo_folder = hou.node('/obj').createNode('geo', node_name='InBetween_ghost_folder')            
                    ghost_mat_folder = ghost_geo_folder.createNode('shopnet', 'ghost_shaders')
                    ghost_mat_folder.moveToGoodPosition()
                    ghost_geo_folder.setColor(hou.Color((0.3,0.3,0.3)))
                    ghost_geo_folder.setSelectableInViewport(0)
                    ghost_geo_folder.hide(1)
                    self.createGhost(ghost_mat_folder, ghost_geo_folder, ghosts)

    def locationChooser(self, menu):
        """Choose location for a new selection set item in radial menu
        
        INPUTS:
        menu -- radial menu object
        """
        if menu.item(hou.radialItemLocation.TopRight) == None:
            return hou.radialItemLocation.TopRight

        elif menu.item(hou.radialItemLocation.Right) == None:
            return hou.radialItemLocation.Right

        elif menu.item(hou.radialItemLocation.BottomRight) == None:
            return hou.radialItemLocation.BottomRight

        elif menu.item(hou.radialItemLocation.Bottom) == None:
            return hou.radialItemLocation.Bottom

        elif menu.item(hou.radialItemLocation.BottomLeft) == None:
            return hou.radialItemLocation.BottomLeft

        elif menu.item(hou.radialItemLocation.Left) == None:
            return hou.radialItemLocation.Left

        elif menu.item(hou.radialItemLocation.TopLeft) == None:
            return hou.radialItemLocation.TopLeft
        else:
            return hou.radialItemLocation.Top

    def createNewSelectionSet(self):
        """Create a new quick selection set from the selected nodes an add it to the radial menu."""
        new_name = hou.ui.readInput('Enter some name', buttons=('OK', 'Cancel'), default_choice=0, 
                            close_choice=1, title='Create selection set', initial_contents='Set_01')
        name = new_name[1]
        choice = new_name[0]
        if choice == 0:
            n = hou.selectedNodes()
            new_list = []
            for i in n:
                new_list.append(i.path())
            
            if hou.ui.radialMenu("selection_sets") == None:
                new_menu = hou.ui.createRadialMenu("selection_sets", "Selection Sets")
                new_menu.setCategories('Selection')
            new_menu = hou.ui.radialMenu("selection_sets")
            location = self.locationChooser(new_menu)
            new_menu.createScriptItem(location, label=name, 
                                    script='new_set = ' + str(new_list) + '\nfor i in new_set: \n    if hou.node(i):\n        hou.node(i).setSelected(True)')
            new_menu.save(hou.expandString('$HOUDINI_USER_PREF_DIR') + '/radialmenu/selection_sets.radialmenu')


