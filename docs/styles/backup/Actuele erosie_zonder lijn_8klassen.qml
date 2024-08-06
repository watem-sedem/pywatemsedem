<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyLocal="1" hasScaleBasedVisibilityFlag="0" labelsEnabled="0" readOnly="0" maxScale="0" simplifyDrawingTol="1" simplifyAlgorithm="0" styleCategories="AllStyleCategories" minScale="1e+08" simplifyMaxScale="1" version="3.4.4-Madeira" simplifyDrawingHints="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 enableorderby="0" type="RuleRenderer" symbollevels="0" forceraster="0">
    <rules key="{3353b064-c86a-4763-b2b8-9d8600b20587}">
      <rule symbol="0" label=">30" key="{7dccc4a4-4342-429f-a992-9c05a5e29d57}" filter="&quot;avg_act_er&quot; >= -10000000.000000 AND &quot;avg_act_er&quot; &lt;= -30.000000"/>
      <rule symbol="1" label="25-30" key="{9222472c-31fa-4974-9668-a142bdab2d8a}" filter="&quot;avg_act_er&quot; > -30.000000 AND &quot;avg_act_er&quot; &lt;= -25.000000"/>
      <rule symbol="2" label="20-25" key="{e2ca9bc0-0b56-4d57-a8c3-0825e51f5a91}" filter="&quot;avg_act_er&quot; > -25.000000 AND &quot;avg_act_er&quot; &lt;= -20.000000"/>
      <rule symbol="3" label="15-20" key="{d44bb77a-bcc5-4fa8-95e0-ef4f35345d3c}" filter="&quot;avg_act_er&quot; > -20.000000 AND &quot;avg_act_er&quot; &lt;= -15.000000"/>
      <rule symbol="4" label="10-15" key="{157fae45-a0a9-4b03-a35a-748c155c9547}" filter="&quot;avg_act_er&quot; > -15.000000 AND &quot;avg_act_er&quot; &lt;= -10.000000"/>
      <rule symbol="5" label="5-10" key="{3b4b9b21-2edf-4a99-8d7e-877e034e2c4e}" filter="&quot;avg_act_er&quot; > -10.000000 AND &quot;avg_act_er&quot; &lt;= -5.000000"/>
      <rule symbol="6" label="0 - 5" key="{d0ee89fa-3fe9-48e2-ac6c-07359a26c96e}" filter="&quot;avg_act_er&quot; > -5.000000 AND &quot;avg_act_er&quot; &lt;= 0.000000"/>
      <rule symbol="7" label="netto sedimentatie" key="{59f2e1c3-bad1-4039-aab9-1ad44e067122}" filter="ELSE"/>
    </rules>
    <symbols>
      <symbol alpha="1" type="fill" name="0" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="188,0,40,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,0"/>
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
      <symbol alpha="1" type="fill" name="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="227,26,28,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="no"/>
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
      <symbol alpha="1" type="fill" name="2" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="250,102,16,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="no"/>
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
      <symbol alpha="1" type="fill" name="3" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="242,135,27,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="no"/>
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
      <symbol alpha="1" type="fill" name="4" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="249,224,98,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="no"/>
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
      <symbol alpha="1" type="fill" name="5" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="246,246,163,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="no"/>
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
      <symbol alpha="1" type="fill" name="6" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="254,254,225,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,0"/>
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
      <symbol alpha="1" type="fill" name="7" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" locked="0" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="217,217,217,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,0"/>
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
    <DiagramCategory penAlpha="255" diagramOrientation="Up" scaleBasedVisibility="0" enabled="0" barWidth="5" maxScaleDenominator="1e+08" opacity="1" sizeScale="3x:0,0,0,0,0,0" lineSizeScale="3x:0,0,0,0,0,0" labelPlacementMethod="XHeight" height="15" backgroundColor="#ffffff" rotationOffset="270" penWidth="0" backgroundAlpha="255" penColor="#000000" scaleDependency="Area" minimumSize="0" minScaleDenominator="0" width="15" lineSizeType="MM" sizeType="MM">
      <fontProperties style="" description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" dist="0" placement="1" linePlacementFlags="18" zIndex="0" priority="0" showAll="1">
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
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="CODE_OBJ"/>
    <alias index="1" name="" field="GWSCOD_V"/>
    <alias index="2" name="" field="GWSNAM_V"/>
    <alias index="3" name="" field="GWSCOD_H"/>
    <alias index="4" name="" field="GWSNAM_H"/>
    <alias index="5" name="" field="GWSGRP_H"/>
    <alias index="6" name="" field="GWSCOD_N"/>
    <alias index="7" name="" field="GWSNAM_N"/>
    <alias index="8" name="" field="ERO_NAM"/>
    <alias index="9" name="" field="STAT_BGV"/>
    <alias index="10" name="" field="NR"/>
    <alias index="11" name="" field="ntkerend"/>
    <alias index="12" name="" field="drempels"/>
    <alias index="13" name="" field="contour"/>
    <alias index="14" name="" field="gewasrest"/>
    <alias index="15" name="" field="groenbedek"/>
    <alias index="16" name="" field="GWSCOD"/>
    <alias index="17" name="" field="Lndgbrk"/>
    <alias index="18" name="" field="Grasbuffer"/>
    <alias index="19" name="" field="BG"/>
    <alias index="20" name="" field="sum_act_er"/>
    <alias index="21" name="" field="avg_act_er"/>
    <alias index="22" name="" field="std_act_er"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="CODE_OBJ" applyOnUpdate="0"/>
    <default expression="" field="GWSCOD_V" applyOnUpdate="0"/>
    <default expression="" field="GWSNAM_V" applyOnUpdate="0"/>
    <default expression="" field="GWSCOD_H" applyOnUpdate="0"/>
    <default expression="" field="GWSNAM_H" applyOnUpdate="0"/>
    <default expression="" field="GWSGRP_H" applyOnUpdate="0"/>
    <default expression="" field="GWSCOD_N" applyOnUpdate="0"/>
    <default expression="" field="GWSNAM_N" applyOnUpdate="0"/>
    <default expression="" field="ERO_NAM" applyOnUpdate="0"/>
    <default expression="" field="STAT_BGV" applyOnUpdate="0"/>
    <default expression="" field="NR" applyOnUpdate="0"/>
    <default expression="" field="ntkerend" applyOnUpdate="0"/>
    <default expression="" field="drempels" applyOnUpdate="0"/>
    <default expression="" field="contour" applyOnUpdate="0"/>
    <default expression="" field="gewasrest" applyOnUpdate="0"/>
    <default expression="" field="groenbedek" applyOnUpdate="0"/>
    <default expression="" field="GWSCOD" applyOnUpdate="0"/>
    <default expression="" field="Lndgbrk" applyOnUpdate="0"/>
    <default expression="" field="Grasbuffer" applyOnUpdate="0"/>
    <default expression="" field="BG" applyOnUpdate="0"/>
    <default expression="" field="sum_act_er" applyOnUpdate="0"/>
    <default expression="" field="avg_act_er" applyOnUpdate="0"/>
    <default expression="" field="std_act_er" applyOnUpdate="0"/>
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
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="CODE_OBJ"/>
    <constraint exp="" desc="" field="GWSCOD_V"/>
    <constraint exp="" desc="" field="GWSNAM_V"/>
    <constraint exp="" desc="" field="GWSCOD_H"/>
    <constraint exp="" desc="" field="GWSNAM_H"/>
    <constraint exp="" desc="" field="GWSGRP_H"/>
    <constraint exp="" desc="" field="GWSCOD_N"/>
    <constraint exp="" desc="" field="GWSNAM_N"/>
    <constraint exp="" desc="" field="ERO_NAM"/>
    <constraint exp="" desc="" field="STAT_BGV"/>
    <constraint exp="" desc="" field="NR"/>
    <constraint exp="" desc="" field="ntkerend"/>
    <constraint exp="" desc="" field="drempels"/>
    <constraint exp="" desc="" field="contour"/>
    <constraint exp="" desc="" field="gewasrest"/>
    <constraint exp="" desc="" field="groenbedek"/>
    <constraint exp="" desc="" field="GWSCOD"/>
    <constraint exp="" desc="" field="Lndgbrk"/>
    <constraint exp="" desc="" field="Grasbuffer"/>
    <constraint exp="" desc="" field="BG"/>
    <constraint exp="" desc="" field="sum_act_er"/>
    <constraint exp="" desc="" field="avg_act_er"/>
    <constraint exp="" desc="" field="std_act_er"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="&quot;sum_act_er&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column type="field" hidden="0" name="CODE_OBJ" width="-1"/>
      <column type="field" hidden="0" name="GWSCOD_V" width="-1"/>
      <column type="field" hidden="0" name="GWSNAM_V" width="-1"/>
      <column type="field" hidden="0" name="GWSCOD_H" width="-1"/>
      <column type="field" hidden="0" name="GWSNAM_H" width="-1"/>
      <column type="field" hidden="0" name="GWSGRP_H" width="-1"/>
      <column type="field" hidden="0" name="GWSCOD_N" width="-1"/>
      <column type="field" hidden="0" name="GWSNAM_N" width="-1"/>
      <column type="field" hidden="0" name="ERO_NAM" width="-1"/>
      <column type="field" hidden="0" name="STAT_BGV" width="-1"/>
      <column type="field" hidden="0" name="NR" width="-1"/>
      <column type="field" hidden="0" name="ntkerend" width="-1"/>
      <column type="field" hidden="0" name="drempels" width="-1"/>
      <column type="field" hidden="0" name="contour" width="-1"/>
      <column type="field" hidden="0" name="gewasrest" width="-1"/>
      <column type="field" hidden="0" name="groenbedek" width="-1"/>
      <column type="field" hidden="0" name="GWSCOD" width="-1"/>
      <column type="field" hidden="0" name="Lndgbrk" width="-1"/>
      <column type="field" hidden="0" name="Grasbuffer" width="-1"/>
      <column type="field" hidden="0" name="BG" width="-1"/>
      <column type="field" hidden="0" name="sum_act_er" width="-1"/>
      <column type="field" hidden="0" name="avg_act_er" width="-1"/>
      <column type="field" hidden="0" name="std_act_er" width="-1"/>
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
    <field name="BG" editable="1"/>
    <field name="CODE_OBJ" editable="1"/>
    <field name="ERO_NAM" editable="1"/>
    <field name="GWSCOD" editable="1"/>
    <field name="GWSCOD_H" editable="1"/>
    <field name="GWSCOD_N" editable="1"/>
    <field name="GWSCOD_V" editable="1"/>
    <field name="GWSGRP_H" editable="1"/>
    <field name="GWSNAM_H" editable="1"/>
    <field name="GWSNAM_N" editable="1"/>
    <field name="GWSNAM_V" editable="1"/>
    <field name="Grasbuffer" editable="1"/>
    <field name="Lndgbrk" editable="1"/>
    <field name="NR" editable="1"/>
    <field name="STAT_BGV" editable="1"/>
    <field name="avg_act_er" editable="1"/>
    <field name="contour" editable="1"/>
    <field name="drempels" editable="1"/>
    <field name="gewasrest" editable="1"/>
    <field name="groenbedek" editable="1"/>
    <field name="ntkerend" editable="1"/>
    <field name="std_act_er" editable="1"/>
    <field name="sum_act_er" editable="1"/>
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
    <field labelOnTop="0" name="ntkerend"/>
    <field labelOnTop="0" name="std_act_er"/>
    <field labelOnTop="0" name="sum_act_er"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>CODE_OBJ</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
