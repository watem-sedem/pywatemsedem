<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" simplifyLocal="1" maxScale="0" simplifyMaxScale="1" version="3.4.4-Madeira" labelsEnabled="0" hasScaleBasedVisibilityFlag="0" minScale="1e+08" styleCategories="AllStyleCategories" simplifyDrawingTol="1" simplifyDrawingHints="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" forceraster="0" type="RuleRenderer" enableorderby="0">
    <rules key="{d5f3a0ba-96ac-4592-bdc0-0339df67c1c6}">
      <rule symbol="0" key="{667cfb97-1b53-4bc3-ae15-c4c2d1458ba7}" filter="&quot;avg_act_er&quot; >= -100000000000.000000 AND &quot;avg_act_er&quot; &lt;= -20.000000" label=">20"/>
      <rule symbol="1" key="{ccb5b744-f68d-4302-aa56-fde269a3bc67}" filter="&quot;avg_act_er&quot; > -20.000000 AND &quot;avg_act_er&quot; &lt;= -15.000000" label="15-20"/>
      <rule symbol="2" key="{c6bc2eb2-1bef-4211-853c-6c8e7b95098a}" filter="&quot;avg_act_er&quot; > -15.000000 AND &quot;avg_act_er&quot; &lt;= -10.000000" label="10-15"/>
      <rule symbol="3" key="{03cec1d5-37dd-45e2-879f-424cfdbac4a0}" filter="&quot;avg_act_er&quot; > -10.000000 AND &quot;avg_act_er&quot; &lt;= -5.000000" label="5-10"/>
      <rule symbol="4" key="{f41680b2-1471-4e8f-9126-8853a9ac8352}" filter="&quot;avg_act_er&quot; > -5.000000 AND &quot;avg_act_er&quot; &lt;= 0.000000" label="0-5"/>
      <rule symbol="5" key="{a0cd6f4f-a48c-4707-80b1-b652aefd3a4a}" filter="ELSE"/>
    </rules>
    <symbols>
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="0">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="182,91,44,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="1">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="216,102,35,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="2">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="242,145,28,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="3">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="250,209,85,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="4">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="255,255,128,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
      <symbol force_rhr="0" alpha="1" clip_to_extent="1" type="fill" name="5">
        <layer enabled="1" locked="0" pass="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="196,60,57,0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
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
    <DiagramCategory penAlpha="255" scaleBasedVisibility="0" sizeType="MM" backgroundAlpha="255" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" height="15" lineSizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minScaleDenominator="0" opacity="1" minimumSize="0" lineSizeType="MM" scaleDependency="Area" diagramOrientation="Up" penWidth="0" maxScaleDenominator="1e+08" labelPlacementMethod="XHeight" penColor="#000000" width="15" enabled="0" barWidth="5">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#000000" label="" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" showAll="1" dist="0" priority="0" zIndex="0" placement="1" obstacle="0">
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
    <field name="CODE_OBJ">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSCOD_V">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSNAM_V">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSCOD_H">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSNAM_H">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSGRP_H">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSCOD_N">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSNAM_N">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ERO_NAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="STAT_BGV">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="NR">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ntkerend">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="drempels">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="contour">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="gewasrest">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="groenbedek">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GWSCOD">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Lndgbrk">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Grasbuffer">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BG">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sum_act_er">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="avg_act_er">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="std_act_er">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="layer">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="path">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="CODE_OBJ" name=""/>
    <alias index="1" field="GWSCOD_V" name=""/>
    <alias index="2" field="GWSNAM_V" name=""/>
    <alias index="3" field="GWSCOD_H" name=""/>
    <alias index="4" field="GWSNAM_H" name=""/>
    <alias index="5" field="GWSGRP_H" name=""/>
    <alias index="6" field="GWSCOD_N" name=""/>
    <alias index="7" field="GWSNAM_N" name=""/>
    <alias index="8" field="ERO_NAM" name=""/>
    <alias index="9" field="STAT_BGV" name=""/>
    <alias index="10" field="NR" name=""/>
    <alias index="11" field="ntkerend" name=""/>
    <alias index="12" field="drempels" name=""/>
    <alias index="13" field="contour" name=""/>
    <alias index="14" field="gewasrest" name=""/>
    <alias index="15" field="groenbedek" name=""/>
    <alias index="16" field="GWSCOD" name=""/>
    <alias index="17" field="Lndgbrk" name=""/>
    <alias index="18" field="Grasbuffer" name=""/>
    <alias index="19" field="BG" name=""/>
    <alias index="20" field="sum_act_er" name=""/>
    <alias index="21" field="avg_act_er" name=""/>
    <alias index="22" field="std_act_er" name=""/>
    <alias index="23" field="layer" name=""/>
    <alias index="24" field="path" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="CODE_OBJ" expression=""/>
    <default applyOnUpdate="0" field="GWSCOD_V" expression=""/>
    <default applyOnUpdate="0" field="GWSNAM_V" expression=""/>
    <default applyOnUpdate="0" field="GWSCOD_H" expression=""/>
    <default applyOnUpdate="0" field="GWSNAM_H" expression=""/>
    <default applyOnUpdate="0" field="GWSGRP_H" expression=""/>
    <default applyOnUpdate="0" field="GWSCOD_N" expression=""/>
    <default applyOnUpdate="0" field="GWSNAM_N" expression=""/>
    <default applyOnUpdate="0" field="ERO_NAM" expression=""/>
    <default applyOnUpdate="0" field="STAT_BGV" expression=""/>
    <default applyOnUpdate="0" field="NR" expression=""/>
    <default applyOnUpdate="0" field="ntkerend" expression=""/>
    <default applyOnUpdate="0" field="drempels" expression=""/>
    <default applyOnUpdate="0" field="contour" expression=""/>
    <default applyOnUpdate="0" field="gewasrest" expression=""/>
    <default applyOnUpdate="0" field="groenbedek" expression=""/>
    <default applyOnUpdate="0" field="GWSCOD" expression=""/>
    <default applyOnUpdate="0" field="Lndgbrk" expression=""/>
    <default applyOnUpdate="0" field="Grasbuffer" expression=""/>
    <default applyOnUpdate="0" field="BG" expression=""/>
    <default applyOnUpdate="0" field="sum_act_er" expression=""/>
    <default applyOnUpdate="0" field="avg_act_er" expression=""/>
    <default applyOnUpdate="0" field="std_act_er" expression=""/>
    <default applyOnUpdate="0" field="layer" expression=""/>
    <default applyOnUpdate="0" field="path" expression=""/>
  </defaults>
  <constraints>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="CODE_OBJ"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSCOD_V"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSNAM_V"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSCOD_H"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSNAM_H"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSGRP_H"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSCOD_N"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSNAM_N"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="ERO_NAM"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="STAT_BGV"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="NR"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="ntkerend"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="drempels"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="contour"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="gewasrest"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="groenbedek"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="GWSCOD"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Lndgbrk"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Grasbuffer"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="BG"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="sum_act_er"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="avg_act_er"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="std_act_er"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="layer"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="path"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="CODE_OBJ" exp=""/>
    <constraint desc="" field="GWSCOD_V" exp=""/>
    <constraint desc="" field="GWSNAM_V" exp=""/>
    <constraint desc="" field="GWSCOD_H" exp=""/>
    <constraint desc="" field="GWSNAM_H" exp=""/>
    <constraint desc="" field="GWSGRP_H" exp=""/>
    <constraint desc="" field="GWSCOD_N" exp=""/>
    <constraint desc="" field="GWSNAM_N" exp=""/>
    <constraint desc="" field="ERO_NAM" exp=""/>
    <constraint desc="" field="STAT_BGV" exp=""/>
    <constraint desc="" field="NR" exp=""/>
    <constraint desc="" field="ntkerend" exp=""/>
    <constraint desc="" field="drempels" exp=""/>
    <constraint desc="" field="contour" exp=""/>
    <constraint desc="" field="gewasrest" exp=""/>
    <constraint desc="" field="groenbedek" exp=""/>
    <constraint desc="" field="GWSCOD" exp=""/>
    <constraint desc="" field="Lndgbrk" exp=""/>
    <constraint desc="" field="Grasbuffer" exp=""/>
    <constraint desc="" field="BG" exp=""/>
    <constraint desc="" field="sum_act_er" exp=""/>
    <constraint desc="" field="avg_act_er" exp=""/>
    <constraint desc="" field="std_act_er" exp=""/>
    <constraint desc="" field="layer" exp=""/>
    <constraint desc="" field="path" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" width="-1" type="field" name="CODE_OBJ"/>
      <column hidden="0" width="-1" type="field" name="GWSCOD_V"/>
      <column hidden="0" width="-1" type="field" name="GWSNAM_V"/>
      <column hidden="0" width="-1" type="field" name="GWSCOD_H"/>
      <column hidden="0" width="-1" type="field" name="GWSNAM_H"/>
      <column hidden="0" width="-1" type="field" name="GWSGRP_H"/>
      <column hidden="0" width="-1" type="field" name="GWSCOD_N"/>
      <column hidden="0" width="-1" type="field" name="GWSNAM_N"/>
      <column hidden="0" width="-1" type="field" name="ERO_NAM"/>
      <column hidden="0" width="-1" type="field" name="STAT_BGV"/>
      <column hidden="0" width="-1" type="field" name="NR"/>
      <column hidden="0" width="-1" type="field" name="ntkerend"/>
      <column hidden="0" width="-1" type="field" name="drempels"/>
      <column hidden="0" width="-1" type="field" name="contour"/>
      <column hidden="0" width="-1" type="field" name="gewasrest"/>
      <column hidden="0" width="-1" type="field" name="groenbedek"/>
      <column hidden="0" width="-1" type="field" name="GWSCOD"/>
      <column hidden="0" width="-1" type="field" name="Lndgbrk"/>
      <column hidden="0" width="-1" type="field" name="Grasbuffer"/>
      <column hidden="0" width="-1" type="field" name="BG"/>
      <column hidden="0" width="-1" type="field" name="sum_act_er"/>
      <column hidden="0" width="-1" type="field" name="avg_act_er"/>
      <column hidden="0" width="-1" type="field" name="std_act_er"/>
      <column hidden="1" width="-1" type="actions"/>
      <column hidden="0" width="-1" type="field" name="layer"/>
      <column hidden="0" width="-1" type="field" name="path"/>
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
    <field editable="1" name="BG"/>
    <field editable="1" name="CODE_OBJ"/>
    <field editable="1" name="ERO_NAM"/>
    <field editable="1" name="GWSCOD"/>
    <field editable="1" name="GWSCOD_H"/>
    <field editable="1" name="GWSCOD_N"/>
    <field editable="1" name="GWSCOD_V"/>
    <field editable="1" name="GWSGRP_H"/>
    <field editable="1" name="GWSNAM_H"/>
    <field editable="1" name="GWSNAM_N"/>
    <field editable="1" name="GWSNAM_V"/>
    <field editable="1" name="Grasbuffer"/>
    <field editable="1" name="Lndgbrk"/>
    <field editable="1" name="NR"/>
    <field editable="1" name="STAT_BGV"/>
    <field editable="1" name="avg_act_er"/>
    <field editable="1" name="contour"/>
    <field editable="1" name="drempels"/>
    <field editable="1" name="gewasrest"/>
    <field editable="1" name="groenbedek"/>
    <field editable="1" name="layer"/>
    <field editable="1" name="ntkerend"/>
    <field editable="1" name="path"/>
    <field editable="1" name="std_act_er"/>
    <field editable="1" name="sum_act_er"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="BG"/>
    <field labelOnTop="0" name="CODE_OBJ"/>
    <field labelOnTop="0" name="ERO_NAM"/>
    <field labelOnTop="0" name="GWSCOD"/>
    <field labelOnTop="0" name="GWSCOD_H"/>
    <field labelOnTop="0" name="GWSCOD_N"/>
    <field labelOnTop="0" name="GWSCOD_V"/>
    <field labelOnTop="0" name="GWSGRP_H"/>
    <field labelOnTop="0" name="GWSNAM_H"/>
    <field labelOnTop="0" name="GWSNAM_N"/>
    <field labelOnTop="0" name="GWSNAM_V"/>
    <field labelOnTop="0" name="Grasbuffer"/>
    <field labelOnTop="0" name="Lndgbrk"/>
    <field labelOnTop="0" name="NR"/>
    <field labelOnTop="0" name="STAT_BGV"/>
    <field labelOnTop="0" name="avg_act_er"/>
    <field labelOnTop="0" name="contour"/>
    <field labelOnTop="0" name="drempels"/>
    <field labelOnTop="0" name="gewasrest"/>
    <field labelOnTop="0" name="groenbedek"/>
    <field labelOnTop="0" name="layer"/>
    <field labelOnTop="0" name="ntkerend"/>
    <field labelOnTop="0" name="path"/>
    <field labelOnTop="0" name="std_act_er"/>
    <field labelOnTop="0" name="sum_act_er"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>CODE_OBJ</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
