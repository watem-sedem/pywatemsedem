<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyAlgorithm="0" labelsEnabled="0" simplifyDrawingHints="1" hasScaleBasedVisibilityFlag="0" minScale="0" simplifyLocal="1" simplifyMaxScale="1" simplifyDrawingTol="1" readOnly="0" version="3.2.0-Bonn" maxScale="0">
  <renderer-v2 forceraster="0" type="singleSymbol" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol alpha="1" type="fill" clip_to_extent="1" name="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="255,255,178,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory penColor="#000000" penAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" labelPlacementMethod="XHeight" width="15" backgroundColor="#ffffff" height="15" enabled="0" backgroundAlpha="255" rotationOffset="0" opacity="1" scaleDependency="Area" lineSizeType="MM" barWidth="5" minScaleDenominator="-2.14748e+9" sizeType="MM" maxScaleDenominator="-2.14748e+9" minimumSize="0" sizeScale="3x:0,0,0,0,0,0" penWidth="0" diagramOrientation="Up">
      <fontProperties description="MS Shell Dlg 2,7.5,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings dist="0" linePlacementFlags="2" zIndex="0" showAll="1" obstacle="0" priority="0" placement="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option type="Map" name="properties">
          <Option type="Map" name="positionX">
            <Option value="true" type="bool" name="active"/>
            <Option value="ID" type="QString" name="field"/>
            <Option value="2" type="int" name="type"/>
          </Option>
          <Option type="Map" name="positionY">
            <Option value="true" type="bool" name="active"/>
            <Option value="ID" type="QString" name="field"/>
            <Option value="2" type="int" name="type"/>
          </Option>
          <Option type="Map" name="show">
            <Option value="true" type="bool" name="active"/>
            <Option value="ID" type="QString" name="field"/>
            <Option value="2" type="int" name="type"/>
          </Option>
        </Option>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <fieldConfiguration>
    <field name="ID">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="0" type="QString" name="IsMultiline"/>
            <Option value="0" type="QString" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="VALUE">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="0" type="QString" name="IsMultiline"/>
            <Option value="0" type="QString" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="NAME">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="0" type="QString" name="IsMultiline"/>
            <Option value="0" type="QString" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="ID" index="0" name=""/>
    <alias field="VALUE" index="1" name=""/>
    <alias field="NAME" index="2" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="ID" applyOnUpdate="0" expression=""/>
    <default field="VALUE" applyOnUpdate="0" expression=""/>
    <default field="NAME" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="ID" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="VALUE" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="NAME" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="ID" exp=""/>
    <constraint desc="" field="VALUE" exp=""/>
    <constraint desc="" field="NAME" exp=""/>
  </constraintExpressions>
  <attributeactions>
    <defaultAction value="{15c69e01-3c03-4dfa-98d7-adb757b16c23}" key="Canvas"/>
    <actionsetting shortTitle="" isEnabledOnlyWhenEditable="0" id="{cd685efd-819c-454f-ac7c-e7d43d708e7d}" notificationMessage="" capture="0" type="0" action="" icon="" name="">
      <actionScope id="Canvas"/>
      <actionScope id="Feature"/>
      <actionScope id="Field"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig sortExpression="" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column type="field" width="-1" name="ID" hidden="0"/>
      <column type="field" width="-1" name="VALUE" hidden="0"/>
      <column type="field" width="-1" name="NAME" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
    </columns>
  </attributetableconfig>
  <editform>D:/Dropbox (Fluves)/ALBON/Modelberekeningen/Waterlandschap</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>D:/Dropbox (Fluves)/ALBON/Modelberekeningen/Waterlandschap</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="ID"/>
    <field editable="1" name="NAME"/>
    <field editable="1" name="VALUE"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="ID"/>
    <field labelOnTop="0" name="NAME"/>
    <field labelOnTop="0" name="VALUE"/>
  </labelOnTop>
  <widgets/>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <expressionfields/>
  <previewExpression>NAME</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
