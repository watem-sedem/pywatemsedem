<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingTol="1" simplifyMaxScale="1" maxScale="0" labelsEnabled="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" simplifyDrawingHints="1" simplifyAlgorithm="0" readOnly="0" version="3.4.4-Madeira" simplifyLocal="1" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="RuleRenderer" symbollevels="0" enableorderby="0" forceraster="0">
    <rules key="{f55d09b7-58a9-4ee0-8db9-aaf23ef2bf99}">
      <rule label="10" filter=" &quot;cum_perc&quot; &lt;= 10" key="{fbf6c8c5-be0a-4732-a96f-225951485f95}" symbol="0"/>
      <rule label="20" filter=" &quot;cum_perc&quot; &lt;= 20 and  &quot;cum_perc&quot; > 10" key="{55cd59d7-51c5-4eb9-abbb-533dd25744ea}" symbol="1"/>
      <rule label="30" filter=" &quot;cum_perc&quot; &lt;= 30 and  &quot;cum_perc&quot; > 20" key="{80e9c5bf-b9c5-4fe6-b6e0-7df4f74a2fb3}" symbol="2"/>
      <rule label="40" filter=" &quot;cum_perc&quot; &lt;= 40 and  &quot;cum_perc&quot; > 30" key="{cd549ae4-91b8-4656-b533-eaa5b3627712}" symbol="3"/>
      <rule label="50" filter="&quot;cum_perc&quot; > 40" key="{1e1f8c40-6f7e-4e1e-b4a3-7c6e2fdc1a17}" symbol="4"/>
    </rules>
    <symbols>
      <symbol type="fill" clip_to_extent="1" force_rhr="0" name="0" alpha="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="189,0,38,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="fill" clip_to_extent="1" force_rhr="0" name="1" alpha="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="240,59,32,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="fill" clip_to_extent="1" force_rhr="0" name="2" alpha="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="253,141,60,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="fill" clip_to_extent="1" force_rhr="0" name="3" alpha="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="254,204,92,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="fill" clip_to_extent="1" force_rhr="0" name="4" alpha="1">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="255,255,178,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>"ID"</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory opacity="1" labelPlacementMethod="XHeight" lineSizeType="MM" scaleBasedVisibility="0" diagramOrientation="Up" minScaleDenominator="0" sizeType="MM" width="15" enabled="0" penColor="#000000" backgroundColor="#ffffff" rotationOffset="270" barWidth="5" scaleDependency="Area" penWidth="0" sizeScale="3x:0,0,0,0,0,0" height="15" lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0" penAlpha="255" maxScaleDenominator="1e+08" backgroundAlpha="255">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="1" linePlacementFlags="18" dist="0" obstacle="0" priority="0" zIndex="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="ID">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="VALUE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="NAME">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="AREA_HA">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="val">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="row">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="col">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="catchments">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="consider">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="perc">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="cum_perc">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="id_1">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="class">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="export_to_">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="export_val">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="ID" index="0" name=""/>
    <alias field="VALUE" index="1" name=""/>
    <alias field="NAME" index="2" name=""/>
    <alias field="AREA_HA" index="3" name=""/>
    <alias field="val" index="4" name=""/>
    <alias field="row" index="5" name=""/>
    <alias field="col" index="6" name=""/>
    <alias field="catchments" index="7" name=""/>
    <alias field="consider" index="8" name=""/>
    <alias field="perc" index="9" name=""/>
    <alias field="cum_perc" index="10" name=""/>
    <alias field="id_1" index="11" name=""/>
    <alias field="class" index="12" name=""/>
    <alias field="export_to_" index="13" name=""/>
    <alias field="export_val" index="14" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="ID"/>
    <default expression="" applyOnUpdate="0" field="VALUE"/>
    <default expression="" applyOnUpdate="0" field="NAME"/>
    <default expression="" applyOnUpdate="0" field="AREA_HA"/>
    <default expression="" applyOnUpdate="0" field="val"/>
    <default expression="" applyOnUpdate="0" field="row"/>
    <default expression="" applyOnUpdate="0" field="col"/>
    <default expression="" applyOnUpdate="0" field="catchments"/>
    <default expression="" applyOnUpdate="0" field="consider"/>
    <default expression="" applyOnUpdate="0" field="perc"/>
    <default expression="" applyOnUpdate="0" field="cum_perc"/>
    <default expression="" applyOnUpdate="0" field="id_1"/>
    <default expression="" applyOnUpdate="0" field="class"/>
    <default expression="" applyOnUpdate="0" field="export_to_"/>
    <default expression="" applyOnUpdate="0" field="export_val"/>
  </defaults>
  <constraints>
    <constraint constraints="0" unique_strength="0" field="ID" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="VALUE" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="NAME" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="AREA_HA" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="val" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="row" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="col" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="catchments" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="consider" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="perc" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="cum_perc" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="id_1" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="class" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="export_to_" exp_strength="0" notnull_strength="0"/>
    <constraint constraints="0" unique_strength="0" field="export_val" exp_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="ID" exp=""/>
    <constraint desc="" field="VALUE" exp=""/>
    <constraint desc="" field="NAME" exp=""/>
    <constraint desc="" field="AREA_HA" exp=""/>
    <constraint desc="" field="val" exp=""/>
    <constraint desc="" field="row" exp=""/>
    <constraint desc="" field="col" exp=""/>
    <constraint desc="" field="catchments" exp=""/>
    <constraint desc="" field="consider" exp=""/>
    <constraint desc="" field="perc" exp=""/>
    <constraint desc="" field="cum_perc" exp=""/>
    <constraint desc="" field="id_1" exp=""/>
    <constraint desc="" field="class" exp=""/>
    <constraint desc="" field="export_to_" exp=""/>
    <constraint desc="" field="export_val" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="&quot;VALUE&quot;">
    <columns>
      <column type="field" width="-1" name="ID" hidden="0"/>
      <column type="field" width="-1" name="VALUE" hidden="0"/>
      <column type="field" width="-1" name="NAME" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
      <column type="field" width="-1" name="AREA_HA" hidden="0"/>
      <column type="field" width="-1" name="id_1" hidden="0"/>
      <column type="field" width="-1" name="perc" hidden="0"/>
      <column type="field" width="-1" name="cum_perc" hidden="0"/>
      <column type="field" width="-1" name="class" hidden="0"/>
      <column type="field" width="-1" name="val" hidden="0"/>
      <column type="field" width="-1" name="row" hidden="0"/>
      <column type="field" width="-1" name="col" hidden="0"/>
      <column type="field" width="-1" name="catchments" hidden="0"/>
      <column type="field" width="-1" name="consider" hidden="0"/>
      <column type="field" width="-1" name="export_to_" hidden="0"/>
      <column type="field" width="-1" name="export_val" hidden="0"/>
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
    <field name="AREA_HA" editable="1"/>
    <field name="ID" editable="1"/>
    <field name="NAME" editable="1"/>
    <field name="VALUE" editable="1"/>
    <field name="catchments" editable="1"/>
    <field name="class" editable="1"/>
    <field name="col" editable="1"/>
    <field name="consider" editable="1"/>
    <field name="cum_perc" editable="1"/>
    <field name="export_to_" editable="1"/>
    <field name="export_val" editable="1"/>
    <field name="id_1" editable="1"/>
    <field name="perc" editable="1"/>
    <field name="row" editable="1"/>
    <field name="val" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="AREA_HA" labelOnTop="0"/>
    <field name="ID" labelOnTop="0"/>
    <field name="NAME" labelOnTop="0"/>
    <field name="VALUE" labelOnTop="0"/>
    <field name="catchments" labelOnTop="0"/>
    <field name="class" labelOnTop="0"/>
    <field name="col" labelOnTop="0"/>
    <field name="consider" labelOnTop="0"/>
    <field name="cum_perc" labelOnTop="0"/>
    <field name="export_to_" labelOnTop="0"/>
    <field name="export_val" labelOnTop="0"/>
    <field name="id_1" labelOnTop="0"/>
    <field name="perc" labelOnTop="0"/>
    <field name="row" labelOnTop="0"/>
    <field name="val" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>ID</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
