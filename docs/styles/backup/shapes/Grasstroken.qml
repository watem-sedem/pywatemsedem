<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" readOnly="0" simplifyDrawingHints="1" simplifyAlgorithm="0" labelsEnabled="0" maxScale="0" version="3.4.4-Madeira" simplifyLocal="1" simplifyMaxScale="1" styleCategories="AllStyleCategories" minScale="1e+08" simplifyDrawingTol="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" enableorderby="0" type="singleSymbol" forceraster="0">
    <symbols>
      <symbol force_rhr="0" type="fill" clip_to_extent="1" alpha="1" name="0">
        <layer class="SimpleFill" enabled="1" locked="0" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="148,255,0,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
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
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory minScaleDenominator="0" opacity="1" maxScaleDenominator="1e+08" barWidth="5" penAlpha="255" diagramOrientation="Up" backgroundAlpha="255" penWidth="0" lineSizeScale="3x:0,0,0,0,0,0" scaleDependency="Area" sizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" penColor="#000000" minimumSize="0" sizeType="MM" scaleBasedVisibility="0" labelPlacementMethod="XHeight" rotationOffset="270" backgroundColor="#ffffff" height="15" width="15" enabled="0">
      <fontProperties style="" description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="1" priority="0" obstacle="0" zIndex="0" linePlacementFlags="18" dist="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="NR">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BREEDTE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="C_fctr_ups">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="C_factor">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="KTC_upstr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="KTC">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SediOut">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SediIn">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Eff">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="AREA">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="NR" index="0" name=""/>
    <alias field="BREEDTE" index="1" name=""/>
    <alias field="C_fctr_ups" index="2" name=""/>
    <alias field="C_factor" index="3" name=""/>
    <alias field="KTC_upstr" index="4" name=""/>
    <alias field="KTC" index="5" name=""/>
    <alias field="SediOut" index="6" name=""/>
    <alias field="SediIn" index="7" name=""/>
    <alias field="Eff" index="8" name=""/>
    <alias field="AREA" index="9" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="NR"/>
    <default expression="" applyOnUpdate="0" field="BREEDTE"/>
    <default expression="" applyOnUpdate="0" field="C_fctr_ups"/>
    <default expression="" applyOnUpdate="0" field="C_factor"/>
    <default expression="" applyOnUpdate="0" field="KTC_upstr"/>
    <default expression="" applyOnUpdate="0" field="KTC"/>
    <default expression="" applyOnUpdate="0" field="SediOut"/>
    <default expression="" applyOnUpdate="0" field="SediIn"/>
    <default expression="" applyOnUpdate="0" field="Eff"/>
    <default expression="" applyOnUpdate="0" field="AREA"/>
  </defaults>
  <constraints>
    <constraint constraints="0" notnull_strength="0" field="NR" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="BREEDTE" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="C_fctr_ups" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="C_factor" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="KTC_upstr" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="KTC" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="SediOut" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="SediIn" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="Eff" unique_strength="0" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" field="AREA" unique_strength="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="NR"/>
    <constraint desc="" exp="" field="BREEDTE"/>
    <constraint desc="" exp="" field="C_fctr_ups"/>
    <constraint desc="" exp="" field="C_factor"/>
    <constraint desc="" exp="" field="KTC_upstr"/>
    <constraint desc="" exp="" field="KTC"/>
    <constraint desc="" exp="" field="SediOut"/>
    <constraint desc="" exp="" field="SediIn"/>
    <constraint desc="" exp="" field="Eff"/>
    <constraint desc="" exp="" field="AREA"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="">
    <columns>
      <column type="field" hidden="0" name="NR" width="-1"/>
      <column type="field" hidden="0" name="BREEDTE" width="-1"/>
      <column type="field" hidden="0" name="C_fctr_ups" width="-1"/>
      <column type="field" hidden="0" name="C_factor" width="-1"/>
      <column type="field" hidden="0" name="KTC_upstr" width="-1"/>
      <column type="field" hidden="0" name="KTC" width="-1"/>
      <column type="field" hidden="0" name="SediOut" width="-1"/>
      <column type="field" hidden="0" name="SediIn" width="-1"/>
      <column type="field" hidden="0" name="Eff" width="-1"/>
      <column type="field" hidden="0" name="AREA" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
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
    <field name="AREA" editable="1"/>
    <field name="BREEDTE" editable="1"/>
    <field name="C_factor" editable="1"/>
    <field name="C_fctr_ups" editable="1"/>
    <field name="Eff" editable="1"/>
    <field name="KTC" editable="1"/>
    <field name="KTC_upstr" editable="1"/>
    <field name="NR" editable="1"/>
    <field name="SediIn" editable="1"/>
    <field name="SediOut" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="AREA"/>
    <field labelOnTop="0" name="BREEDTE"/>
    <field labelOnTop="0" name="C_factor"/>
    <field labelOnTop="0" name="C_fctr_ups"/>
    <field labelOnTop="0" name="Eff"/>
    <field labelOnTop="0" name="KTC"/>
    <field labelOnTop="0" name="KTC_upstr"/>
    <field labelOnTop="0" name="NR"/>
    <field labelOnTop="0" name="SediIn"/>
    <field labelOnTop="0" name="SediOut"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>NR</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
