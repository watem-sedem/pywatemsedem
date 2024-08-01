<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingTol="1" labelsEnabled="0" simplifyDrawingHints="1" simplifyLocal="1" simplifyMaxScale="1" styleCategories="AllStyleCategories" maxScale="0" simplifyAlgorithm="0" hasScaleBasedVisibilityFlag="0" readOnly="0" version="3.4.4-Madeira" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" enableorderby="0" type="RuleRenderer" forceraster="0">
    <rules key="{f55d09b7-58a9-4ee0-8db9-aaf23ef2bf99}">
      <rule label="zeer hoog" key="{fbf6c8c5-be0a-4732-a96f-225951485f95}" filter="  &quot;SedArea&quot; >1" symbol="0"/>
      <rule label="hoog" key="{55cd59d7-51c5-4eb9-abbb-533dd25744ea}" filter=" &quot;SedArea&quot; &lt;=1 and  &quot;SedArea&quot; >0.75" symbol="1"/>
      <rule label="gemiddeld" key="{80e9c5bf-b9c5-4fe6-b6e0-7df4f74a2fb3}" filter=" &quot;SedArea&quot; &lt;=0.75 and  &quot;SedArea&quot; >0.5" symbol="2"/>
      <rule label="laag" key="{cd549ae4-91b8-4656-b533-eaa5b3627712}" filter=" &quot;SedArea&quot; &lt;=0.5 and  &quot;SedArea&quot; >0.25" symbol="3"/>
      <rule label="zeer laag" key="{1e1f8c40-6f7e-4e1e-b4a3-7c6e2fdc1a17}" filter=" &quot;SedArea&quot; &lt;=0.25" symbol="4"/>
    </rules>
    <symbols>
      <symbol name="0" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="189,0,38,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="240,59,32,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="2" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="253,141,60,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="3" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="254,204,92,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="4" type="fill" force_rhr="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" pass="0" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="255,255,178,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <customproperties>
    <property key="dualview/previewExpressions" value="&quot;ID&quot;"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory enabled="0" sizeType="MM" sizeScale="3x:0,0,0,0,0,0" width="15" labelPlacementMethod="XHeight" penColor="#000000" height="15" minimumSize="0" opacity="1" maxScaleDenominator="1e+08" rotationOffset="270" minScaleDenominator="0" penWidth="0" barWidth="5" penAlpha="255" lineSizeType="MM" backgroundAlpha="255" scaleBasedVisibility="0" backgroundColor="#ffffff" scaleDependency="Area" lineSizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" obstacle="0" zIndex="0" dist="0" linePlacementFlags="18" placement="1" showAll="1">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="OBJECTID">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="A1_CODE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="A1_NAAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="A0_CODE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="TA1">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Shape_Leng">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Shape_Area">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="CELLS">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="MIN">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="MAX">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SUM_KG">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="MEAN">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="VARIANCE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="STDDEV">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SUM_TONS">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SedArea">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="SedCells">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="OBJECTID" index="0"/>
    <alias name="" field="A1_CODE" index="1"/>
    <alias name="" field="A1_NAAM" index="2"/>
    <alias name="" field="A0_CODE" index="3"/>
    <alias name="" field="TA1" index="4"/>
    <alias name="" field="Shape_Leng" index="5"/>
    <alias name="" field="Shape_Area" index="6"/>
    <alias name="" field="CELLS" index="7"/>
    <alias name="" field="MIN" index="8"/>
    <alias name="" field="MAX" index="9"/>
    <alias name="" field="SUM_KG" index="10"/>
    <alias name="" field="MEAN" index="11"/>
    <alias name="" field="VARIANCE" index="12"/>
    <alias name="" field="STDDEV" index="13"/>
    <alias name="" field="SUM_TONS" index="14"/>
    <alias name="" field="SedArea" index="15"/>
    <alias name="" field="SedCells" index="16"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="OBJECTID" applyOnUpdate="0"/>
    <default expression="" field="A1_CODE" applyOnUpdate="0"/>
    <default expression="" field="A1_NAAM" applyOnUpdate="0"/>
    <default expression="" field="A0_CODE" applyOnUpdate="0"/>
    <default expression="" field="TA1" applyOnUpdate="0"/>
    <default expression="" field="Shape_Leng" applyOnUpdate="0"/>
    <default expression="" field="Shape_Area" applyOnUpdate="0"/>
    <default expression="" field="CELLS" applyOnUpdate="0"/>
    <default expression="" field="MIN" applyOnUpdate="0"/>
    <default expression="" field="MAX" applyOnUpdate="0"/>
    <default expression="" field="SUM_KG" applyOnUpdate="0"/>
    <default expression="" field="MEAN" applyOnUpdate="0"/>
    <default expression="" field="VARIANCE" applyOnUpdate="0"/>
    <default expression="" field="STDDEV" applyOnUpdate="0"/>
    <default expression="" field="SUM_TONS" applyOnUpdate="0"/>
    <default expression="" field="SedArea" applyOnUpdate="0"/>
    <default expression="" field="SedCells" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="OBJECTID"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="A1_CODE"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="A1_NAAM"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="A0_CODE"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="TA1"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="Shape_Leng"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="Shape_Area"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="CELLS"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="MIN"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="MAX"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="SUM_KG"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="MEAN"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="VARIANCE"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="STDDEV"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="SUM_TONS"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="SedArea"/>
    <constraint constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0" field="SedCells"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="OBJECTID" exp=""/>
    <constraint desc="" field="A1_CODE" exp=""/>
    <constraint desc="" field="A1_NAAM" exp=""/>
    <constraint desc="" field="A0_CODE" exp=""/>
    <constraint desc="" field="TA1" exp=""/>
    <constraint desc="" field="Shape_Leng" exp=""/>
    <constraint desc="" field="Shape_Area" exp=""/>
    <constraint desc="" field="CELLS" exp=""/>
    <constraint desc="" field="MIN" exp=""/>
    <constraint desc="" field="MAX" exp=""/>
    <constraint desc="" field="SUM_KG" exp=""/>
    <constraint desc="" field="MEAN" exp=""/>
    <constraint desc="" field="VARIANCE" exp=""/>
    <constraint desc="" field="STDDEV" exp=""/>
    <constraint desc="" field="SUM_TONS" exp=""/>
    <constraint desc="" field="SedArea" exp=""/>
    <constraint desc="" field="SedCells" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;VALUE&quot;" sortOrder="0">
    <columns>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" name="OBJECTID" type="field" hidden="0"/>
      <column width="-1" name="A1_CODE" type="field" hidden="0"/>
      <column width="-1" name="A1_NAAM" type="field" hidden="0"/>
      <column width="-1" name="A0_CODE" type="field" hidden="0"/>
      <column width="-1" name="TA1" type="field" hidden="0"/>
      <column width="-1" name="Shape_Leng" type="field" hidden="0"/>
      <column width="-1" name="Shape_Area" type="field" hidden="0"/>
      <column width="-1" name="CELLS" type="field" hidden="0"/>
      <column width="-1" name="MIN" type="field" hidden="0"/>
      <column width="-1" name="MAX" type="field" hidden="0"/>
      <column width="-1" name="SUM_KG" type="field" hidden="0"/>
      <column width="-1" name="MEAN" type="field" hidden="0"/>
      <column width="-1" name="VARIANCE" type="field" hidden="0"/>
      <column width="-1" name="STDDEV" type="field" hidden="0"/>
      <column width="-1" name="SUM_TONS" type="field" hidden="0"/>
      <column width="-1" name="SedArea" type="field" hidden="0"/>
      <column width="-1" name="SedCells" type="field" hidden="0"/>
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
    <field editable="1" name="A0_CODE"/>
    <field editable="1" name="A1_CODE"/>
    <field editable="1" name="A1_NAAM"/>
    <field editable="1" name="AREA_HA"/>
    <field editable="1" name="CELLS"/>
    <field editable="1" name="ID"/>
    <field editable="1" name="MAX"/>
    <field editable="1" name="MEAN"/>
    <field editable="1" name="MIN"/>
    <field editable="1" name="NAME"/>
    <field editable="1" name="OBJECTID"/>
    <field editable="1" name="STDDEV"/>
    <field editable="1" name="SUM_KG"/>
    <field editable="1" name="SUM_TONS"/>
    <field editable="1" name="SedArea"/>
    <field editable="1" name="SedCells"/>
    <field editable="1" name="Shape_Area"/>
    <field editable="1" name="Shape_Leng"/>
    <field editable="1" name="TA1"/>
    <field editable="1" name="VALUE"/>
    <field editable="1" name="VARIANCE"/>
    <field editable="1" name="catchments"/>
    <field editable="1" name="class"/>
    <field editable="1" name="col"/>
    <field editable="1" name="consider"/>
    <field editable="1" name="cum_perc"/>
    <field editable="1" name="export_to_"/>
    <field editable="1" name="export_val"/>
    <field editable="1" name="id_1"/>
    <field editable="1" name="perc"/>
    <field editable="1" name="row"/>
    <field editable="1" name="val"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="A0_CODE"/>
    <field labelOnTop="0" name="A1_CODE"/>
    <field labelOnTop="0" name="A1_NAAM"/>
    <field labelOnTop="0" name="AREA_HA"/>
    <field labelOnTop="0" name="CELLS"/>
    <field labelOnTop="0" name="ID"/>
    <field labelOnTop="0" name="MAX"/>
    <field labelOnTop="0" name="MEAN"/>
    <field labelOnTop="0" name="MIN"/>
    <field labelOnTop="0" name="NAME"/>
    <field labelOnTop="0" name="OBJECTID"/>
    <field labelOnTop="0" name="STDDEV"/>
    <field labelOnTop="0" name="SUM_KG"/>
    <field labelOnTop="0" name="SUM_TONS"/>
    <field labelOnTop="0" name="SedArea"/>
    <field labelOnTop="0" name="SedCells"/>
    <field labelOnTop="0" name="Shape_Area"/>
    <field labelOnTop="0" name="Shape_Leng"/>
    <field labelOnTop="0" name="TA1"/>
    <field labelOnTop="0" name="VALUE"/>
    <field labelOnTop="0" name="VARIANCE"/>
    <field labelOnTop="0" name="catchments"/>
    <field labelOnTop="0" name="class"/>
    <field labelOnTop="0" name="col"/>
    <field labelOnTop="0" name="consider"/>
    <field labelOnTop="0" name="cum_perc"/>
    <field labelOnTop="0" name="export_to_"/>
    <field labelOnTop="0" name="export_val"/>
    <field labelOnTop="0" name="id_1"/>
    <field labelOnTop="0" name="perc"/>
    <field labelOnTop="0" name="row"/>
    <field labelOnTop="0" name="val"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>ID</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
