#Author-Xiaodong Liang, Autodesk
#Design Text on Surface as Extrude Feature

import adsk.core, adsk.fusion, traceback #,os
#import sys

#global definition

#command ID
commandIdOnPanel = 'id_TextOnSurface'
#enviornment to use the command
workspaceToUse = 'FusionSolidEnvironment'
#panel to put the button
panelToUse = 'SolidCreatePanel'

# global set of event handlers to keep them referenced for the duration of the command

#for command
handlers = []
#for command dialog
handlers_dialog = []

# the text box to show warning
warning_text_input = None

#selected face
#note: because of an issue of Fusion API, the command dialog does not provide the
#selection input. The user needs to select a surface in advance, next run the command
currentSel = None

#some default params for sketch text
defaultFontHeight = 1.0
defaultLetterGap = 0.1
defaultExtrudeDis = 1.0
defaultStartAngle = 0.1
defaultAxisDis = 0

#get edge evaluator from a surface
#Reserved
def get2DEval(cyFace):
     eval2d = None
     for loop in cyFace.loops:
        for coedge in loop.coEdges:
            eval2d = coedge.evaluator
            break
     return eval2d

#get inputs of command dialog
class EmbossTextCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        global warning_text_input
        try:
            app = adsk.core.Application.get()
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            #emboss text instance to store the params
            embossText = EmbossText()
            for input in inputs:
                if input.id == 'textString':
                    embossText.textString = input.value
                elif input.id == 'cylinderFace':
                    embossText.cylinderFace = input.selection(0).entity
                    #global currentSel
                    #currentSel = input.selection(0).entity
                elif input.id == 'fontHeight':
                    embossText.fontHeight = unitsMgr.evaluateExpression(input.expression, "cm")
                elif input.id == 'letterGap':
                    embossText.letterGap = unitsMgr.evaluateExpression(input.expressionOne, "rad")
                elif input.id == 'booleanMethod':
                    embossText.booleanMethod = input.selectedItem.name
                elif input.id == 'extrudeDis':
                    embossText.extrudeDis = unitsMgr.evaluateExpression(input.expression, "cm")
                elif input.id == 'startAngle':
                    embossText.startAngle = unitsMgr.evaluateExpression(input.expressionOne, "rad")
                elif input.id == 'isBold':
                    embossText.isBold = input.value
                elif input.id == 'isItalic':
                    embossText.isItalic = input.value
                elif input.id == 'isUnderlined':
                    embossText.isUnderlined = input.value
                elif input.id == 'textAngle':
                    embossText.textAngle = unitsMgr.evaluateExpression(input.expressionOne, "rad")
                elif input.id == 'isFlipEmboss':
                    embossText.isFlipEmboss = input.value
                elif input.id == 'axisDis':
                    embossText.axisDis = unitsMgr.evaluateExpression(input.expression, "cm")
                #elif input.id == 'fontName':
                #   embossText.fontName = input.selectedItem.name
                if input.id == 'fontName_by_typing':
                    embossText.fontName_by_typing = input.value
                if input.id == 'isFlipDirAtAxis':
                    embossText.isFlipDirAtAxis = input.value


            #try to create the result text feature

            embossText.buildTextFeatures()
            args.isValidResult = True
            warning_text_input.value = ''

        except:
            #if ui:
                #ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            if warning_text_input:
                warning_text_input.value = "Bad Input! This might be due to invalid font name or there is no material for Cut feature"


class EmbossTextCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            global currentSel
            currentSel = None

            #clearn up the handlers of command dialog.
            #next time when the dialog is invoked, all inputs will be created again
            global handlers_dialog
            handlers_dialog = []

            #since the command itself is also running within the callback. DO NOT
            #terminate it
            #adsk.terminate()

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

#Initialize the events and inputs
class EmbossTextCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface

        global currentSel
        if currentSel == None:
            if ui.activeSelections.count > 0:
                currentSel = ui.activeSelections.item(0).entity
            else:
                ui.messageBox('Please select a cylindrical face in advance!')
                return

        try:
            cmd = args.command
            #execution  of the command dialog
            onExecute = EmbossTextCommandExecuteHandler()
            cmd.execute.add(onExecute)
            #preview of the command dialog; use the same workflow of execution
            onExecutePreview = EmbossTextCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            #destroy of the command dialog
            onDestroy = EmbossTextCommandDestroyHandler()
            cmd.destroy.add(onDestroy)

            # keep the handler referenced beyond this function
            handlers_dialog.append(onExecute)
            handlers_dialog.append(onExecutePreview)
            handlers_dialog.append(onDestroy)

            #define the inputs
            inputs = cmd.commandInputs

            #selInput = inputs.addSelectionInput('cylinderFace',
            #'Select a Cylinder Face',
            #'Select a Cylinder Face')
            #selInput.setSelectionLimits(1,1)
            #selInput.addSelectionFilter('CylindricalFaces')

            #text string
            inputs.addStringValueInput('textString', 'Text', '')

            #note: because of an issue of Fusion API, the command dialog does not provide the
            #selection input. The user needs to select a surface in advance, next run the command
            #Reserved these lines for future

            #font list
            #trying to find way to get OS fonts list automatically
            #font_dropdown = inputs.addDropDownCommandInput('fontName','Font Name',2)
            #font_dropdown.listItems.add('Arial',True,'./resources',-1)
            #getOSFonts(font_dropdown)

            #use a workaround to ask the user to input the font name
            #they can check the name from sketch text editing dialog themselves.

            font_name_by_typing = inputs.addStringValueInput('fontName_by_typing', 'Font Name', '')
            #give a default one which should exist
            font_name_by_typing.value = 'Arial'

            #font height
            initFontHeight = adsk.core.ValueInput.createByReal(defaultFontHeight)
            inputs.addValueInput('fontHeight', 'Font Height','cm',initFontHeight)

            #font is bold
            inputs.addBoolValueInput('isBold','Bold',True,'./resources',False)
            #font is italic
            inputs.addBoolValueInput('isItalic','Italic',True,'./resources',False)
            #font is underlined - no use. in UI, underline is also ignored if extruding a text
            #inputs.addBoolValueInput('isUnderlined','Underlined',True,'./resources',False)
            #text angle in the sketch plane
            inputs.addRangeCommandFloatInput('textAngle','Text Angle', 'rad', 0, 6.28,False)
            #text start angle along the parameters range
            startAngleV = inputs.addRangeCommandFloatInput('startAngle','Start Angle', 'rad', 0, 6.28,False)
            #set a default start angle
            startAngleV.expressionOne = '0.1 rad'

            isFlipDirAtAxis = inputs.addBoolValueInput('isFlipDirAtAxis','Flip Direction at Axis',True,'./resources',False)
            isFlipDirAtAxis.value = False

            #the distance of text position along axis direction
            initAxisDis = adsk.core.ValueInput.createByReal(defaultAxisDis)
            inputs.addValueInput('axisDis', 'Distance at Axis', 'cm', initAxisDis)

            #distance of each letter
            inputs.addRangeCommandFloatInput('letterGap','Letter Gap', 'rad', -3.14, 3.14,False)

            #method to create the text feature: Cut or Join
            booleanMethod_dropdown = inputs.addDropDownCommandInput('booleanMethod','Boolean Method',2)
            booleanMethod_dropdown.listItems.add('Cut',True,'./resources',-1)
            booleanMethod_dropdown.listItems.add('Join',False,'./resources',-1)

            #if flip the text feature: e.g. in Cut mode, feature creation might fail because
            #no material the text feature can cut. so flip the feature to the other side that
            #has material.
            isFlipEmboss = inputs.addBoolValueInput('isFlipEmboss','Flip Emboss',True,'./resources',False)
            isFlipEmboss.value = True
            #emboss distance of text feature
            initExtrudeDis = adsk.core.ValueInput.createByReal(defaultExtrudeDis)
            inputs.addValueInput('extrudeDis', 'Emboss Distance', 'cm', initExtrudeDis)

            global warning_text_input
            warning_text_input = inputs.addStringValueInput('warningText', 'Warning', '')
            warning_text_input.isEnabled = False


        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

#Text feature params and creation class
class EmbossText:
    def __init__(self):
        #text string
        self._textString = ''
        #selected face: no use now, reserved
        self._cylinderFace  = None
        #font height
        self._fontHeight = adsk.core.ValueInput.createByReal(defaultFontHeight)
        #distance of each letter
        self._letterGap = adsk.core.ValueInput.createByReal(defaultLetterGap)
        #method to create the text feature
        self._booleanMethod = 1  #1. cut, 0, join
        #emboss distance
        self._extrudeDis = adsk.core.ValueInput.createByReal(defaultExtrudeDis)
        #text start angle along the parameters range
        self._startAngle = adsk.core.ValueInput.createByReal(defaultStartAngle)
        #font name
        self._fontName = 'Arial'
        #is font bold
        self._isBold = False
        #is font italic
        self._isItalic = False
        #is font underlined
        self._isUnderlined = False
        #text angle in the sketch plane
        self._textAngle = 0
        #the distance of text position along axis direction
        self._axisDis = 0
        #if flip the text feature: e.g. in Cut mode, feature creation might fail because
        #no material the text feature can cut. so flip the feature to the other side that
        #has material.
        self._isFlipEmboss = False
        #workaround for font name
        self._fontName_by_typing = 'Arial'
          #is flip direction at axis
        self._isFlipDirAtAxis = False

    #properties
    @property
    def textString(self):
        return self._textString
    @textString.setter
    def textString(self, value):
        self._textString = value

    @property
    def cylinderFace(self):
        return self._cylinderFace
    @cylinderFace.setter
    def cylinderFace(self, value):
        self._cylinderFace = value

    @property
    def fontName(self):
        return self._fontName
    @fontName.setter
    def fontName(self, value):
        self._fontName = value

    @property
    def fontHeight(self):
        return self._fontHeight
    @fontHeight.setter
    def fontHeight(self, value):
        self._fontHeight = value

    @property
    def isBold(self):
        return self._isBold
    @isBold.setter
    def isBold(self, value):
        self._isBold = value

    @property
    def isItalic(self):
        return self._isItalic
    @isItalic.setter
    def isItalic(self, value):
        self._isItalic = value

    @property
    def isUnderlined(self):
        return self._isUnderlined
    @isUnderlined.setter
    def isUnderlined(self, value):
        self._isUnderlined = value

    @property
    def textAngle(self):
        return self._textAngle
    @textAngle.setter
    def textAngle(self, value):
        self._textAngle = value


    @property
    def isFlipDirAtAxis(self):
        return self._isFlipDirAtAxis
    @isFlipDirAtAxis.setter
    def isFlipDirAtAxis(self, value):
        self._isFlipDirAtAxis = value

    @property
    def axisDis(self):
        return self._axisDis
    @axisDis.setter
    def axisDis(self, value):
        self._axisDis = value

    @property
    def letterGap(self):
        return self._booleanMethod
    @letterGap.setter
    def letterGap(self, value):
        self._booleanMethod = value

    @property
    def booleanMethod(self):
        return self._headHeight
    @booleanMethod.setter
    def booleanMethod(self, value):
        self._headHeight = value

    @property
    def isFlipEmboss(self):
        return self._isFlipEmboss
    @isFlipEmboss.setter
    def isFlipEmboss(self, value):
        self._isFlipEmboss = value

    @property
    def extrudeDis(self):
        return self._extrudeDis
    @extrudeDis.setter
    def extrudeDis(self, value):
        self._extrudeDis = value

    @property
    def startAngle(self):
        return self._startAngle
    @startAngle.setter
    def startAngle(self, value):
        self._startAngle = value

    @property
    def fontName_by_typing(self):
        return self._fontName_by_typing
    @fontName_by_typing.setter
    def fontName_by_typing(self, value):
        self._fontName_by_typing = value

    #try to create the result text feature
    def buildTextFeatures(self):
        app = adsk.core.Application.get()
        ui = app.userInterface

        if self.fontName_by_typing == '':
            ui.messageBox('Please input the font name!')
            return

        product = app.activeProduct
        #design = adsk.fusion.Design.cast(product)
        #current component
        rootComp = product.rootComponent

        global currentSel
        if currentSel!= None:
                #evaluator of the surface
                eval3d = currentSel.geometry.evaluator
                #default start angle in parameters range for the first letter
                thisP = self.startAngle
                #iterate each letter
                for eachLetter in self.textString:
                    try:
                        #get 3D position of this param
                        pt_2d = adsk.core.Point2D.create(0,thisP)
                        (ReturnValue, pt_3d) = eval3d.getPointAtParameter(pt_2d)
                        cons_input =  rootComp.constructionPoints.createInput()
                        cons_input.setByPoint(pt_3d)
                        pts = []
                        pts.append(pt_3d)

                        #normal at this 3D position
                        (ReturnValue, normals) = eval3d.getNormalsAtPoints(pts)
                        print(normals[0].x,normals[0].y,normals[0].z)

                        #U V (X, Y) direction at this 3D position
                        (ReturnValue, partialU, partialV) = eval3d.getFirstDerivative(pt_2d)
                        #create a plane on the 3D position and U V.
                        plane = adsk.core.Plane.create(pt_3d,normals[0])
                        if self.isFlipDirAtAxis:
                            partialU.x = -partialU.x
                            partialU.y = -partialU.y
                            partialU.z = -partialU.z
                            plane.setUVDirections(partialV,partialU)
                        else:
                            plane.setUVDirections(partialV,partialU)
                        cons_planes = rootComp.constructionPlanes
                        cons_planeInput = cons_planes.createInput()
                        cons_planeInput.setByPlane(plane)
                        cons_plane = cons_planes.add(cons_planeInput)

                        #create a sketch from this plane
                        sketches = rootComp.sketches
                        sketch = sketches.add(cons_plane)

                        #create the text of this letter on this sketch
                        sketch_texts = sketch.sketchTexts
                        txt_pos = adsk.core.Point3D.create(pt_3d.x + partialU.x * self.axisDis  ,
                                                           pt_3d.y + partialU.y * self.axisDis  ,
                                                           pt_3d.z + partialU.z * self.axisDis  )


                        txt_pos_in_sketch = sketch.modelToSketchSpace(txt_pos)
                        sketch_text_input = sketch_texts.createInput(eachLetter,
                                                                     self.fontHeight,
                                                                     txt_pos_in_sketch)
                        #parameters of this text

                        #sketch_text_input.fontName = self.fontName
                        sketch_text_input.fontName = self.fontName_by_typing
                        this_letter_in_sketch = sketch_texts.add(sketch_text_input)
                        this_letter_in_sketch.angle = self.textAngle

                        txtStyle = 0
                        if self.isBold:
                            txtStyle = txtStyle + 1
                        if self.isItalic:
                            txtStyle = txtStyle + 2
                        if self.isUnderlined:
                            txtStyle = txtStyle + 4

                        this_letter_in_sketch.textStyle = txtStyle

                    #try to create the text feature

                        extrudes = rootComp.features.extrudeFeatures;

                        if self.booleanMethod == 'Cut':
                            extInput = extrudes.createInput(this_letter_in_sketch,
                                                        adsk.fusion.FeatureOperations.CutFeatureOperation);
                        else:
                            extInput = extrudes.createInput(this_letter_in_sketch,
                                                        adsk.fusion.FeatureOperations.JoinFeatureOperation);

                        if self.isFlipEmboss:
                            thisExtrudeDis = adsk.core.ValueInput.createByReal(-self.extrudeDis)
                        else:
                            thisExtrudeDis = adsk.core.ValueInput.createByReal(self.extrudeDis)
                        extInput.setDistanceExtent(False, thisExtrudeDis)
                        extrudes.add(extInput)
                    except:
                        print('except')

                    #move to the next letter, increase the step by letter gap
                    thisP = thisP + self.letterGap
        else:
             ui.messageBox('Please select a cylindrical face in advance!')

######### scope of add-in definition ###############
def commandDefinitionById(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandDefinition id is not specified')
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(id)
    return commandDefinition_

def commandControlByIdForPanel(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandControl id is not specified')
        return None

    workspaces_ = ui.workspaces
    modelingWorkspace_ = workspaces_.itemById(workspaceToUse)
    toolbarPanels_ = modelingWorkspace_.toolbarPanels
    toolbarPanel_ = toolbarPanels_.itemById(panelToUse)
    toolbarControls_ = toolbarPanel_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox('tobeDeleteObj is not a valid object')

def run(context):
    ui = None
    try:
        commandName = 'Text on Surface'
        commandDescription = "Place text on any surface with its letters distributed along the surface's parametric space"
        commandResources = './resources/command'

        app = adsk.core.Application.get()
        ui = app.userInterface

        commandDefinitions_ = ui.commandDefinitions

        # add a command on create panel in modelling workspace
        workspaces_ = ui.workspaces
        modelingWorkspace_ = workspaces_.itemById(workspaceToUse)
        toolbarPanels_ = modelingWorkspace_.toolbarPanels
        toolbarPanel_ = toolbarPanels_.itemById(panelToUse)
        toolbarControlsPanel_ = toolbarPanel_.controls
        toolbarControlPanel_ = toolbarControlsPanel_.itemById(commandIdOnPanel)
        if not toolbarControlPanel_:
            commandDefinitionPanel_ = commandDefinitions_.itemById(commandIdOnPanel)
            if not commandDefinitionPanel_:
                commandDefinitionPanel_ = commandDefinitions_.addButtonDefinition(commandIdOnPanel, commandName, commandName, commandResources)
                commandDefinitionPanel_.tooltipDescription = commandDescription

            onCommandCreated = EmbossTextCommandCreatedHandler() # CommandCreatedEventHandlerPanel()
            commandDefinitionPanel_.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            toolbarControlPanel_ = toolbarControlsPanel_.addCommand(commandDefinitionPanel_, commandIdOnPanel)
            toolbarControlPanel_.isVisible = True

    except:
        if ui:
            ui.messageBox('AddIn Start Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        objArrayPanel = []

        commandControlPanel_ = commandControlByIdForPanel(commandIdOnPanel)
        if commandControlPanel_:
            objArrayPanel.append(commandControlPanel_)

        commandDefinitionPanel_ = commandDefinitionById(commandIdOnPanel)
        if commandDefinitionPanel_:
            objArrayPanel.append(commandDefinitionPanel_)

        for obj in objArrayPanel:
            destroyObject(ui, obj)

        #adsk.terminate()

    except:
        if ui:
            ui.messageBox('AddIn Stop Failed:\n{}'.format(traceback.format_exc()))
######### end of add-in definition ###############