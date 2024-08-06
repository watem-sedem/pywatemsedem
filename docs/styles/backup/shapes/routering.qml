<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+8" simplifyMaxScale="1" labelsEnabled="0" simplifyAlgorithm="0" maxScale="0" version="3.0.0-Girona" simplifyDrawingTol="1" simplifyLocal="1" simplifyDrawingHints="1" readOnly="0" hasScaleBasedVisibilityFlag="0">
  <renderer-v2 enableorderby="0" symbollevels="0" type="RuleRenderer" forceraster="0">
    <rules key="{fbcb9d02-81d9-4ada-9d8b-24a488978f38}">
      <rule filter="&quot;jump&quot; = 1 and (&quot;lnduSource&quot; != -1) and &quot;part1&quot; !=0" symbol="0" key="{e9819f49-8942-4b0d-a968-90cedcf3cc39}" label="Springen"/>
      <rule filter="&quot;jump&quot; = 1 and &quot;lnduSource&quot; = -1 and &quot;lnduTarg&quot; = -1" symbol="1" key="{62f48520-7352-46e9-b808-dc5bc358f01d}" label="Springen binnen rivier"/>
      <rule filter="&quot;jump&quot; = 0 and &quot;part1&quot; !=0" symbol="2" key="{72c398e6-b809-47f0-9054-6f60333ba724}" label="Routing naar naburige pixel"/>
      <rule filter="&quot;jump&quot; = 0 and &quot;part1&quot; = 0" symbol="3" key="{ad8441ec-8f73-4c2c-a49f-a68a14080e3a}" label="Transportvector gelijk aan 0"/>
    </rules>
    <symbols>
      <symbol clip_to_extent="1" alpha="1" name="0" type="line">
        <layer pass="0" locked="0" class="ArrowLine" enabled="1">
          <prop k="arrow_start_width" v="0"/>
          <prop k="arrow_start_width_unit" v="MM"/>
          <prop k="arrow_start_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="arrow_type" v="0"/>
          <prop k="arrow_width" v="0.6"/>
          <prop k="arrow_width_unit" v="MM"/>
          <prop k="arrow_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_length" v="0.9"/>
          <prop k="head_length_unit" v="MM"/>
          <prop k="head_length_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_thickness" v="1.1"/>
          <prop k="head_thickness_unit" v="MM"/>
          <prop k="head_thickness_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_type" v="0"/>
          <prop k="is_curved" v="1"/>
          <prop k="is_repeated" v="1"/>
          <prop k="offset" v="0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" alpha="1" name="@0@0" type="fill">
            <layer pass="0" locked="0" class="SimpleFill" enabled="1">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="207,84,164,0"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.26"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" alpha="1" name="1" type="line">
        <layer pass="0" locked="0" class="ArrowLine" enabled="1">
          <prop k="arrow_start_width" v="0"/>
          <prop k="arrow_start_width_unit" v="MM"/>
          <prop k="arrow_start_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="arrow_type" v="0"/>
          <prop k="arrow_width" v="0.8"/>
          <prop k="arrow_width_unit" v="MM"/>
          <prop k="arrow_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_length" v="0.9"/>
          <prop k="head_length_unit" v="MM"/>
          <prop k="head_length_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_thickness" v="1.1"/>
          <prop k="head_thickness_unit" v="MM"/>
          <prop k="head_thickness_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_type" v="0"/>
          <prop k="is_curved" v="1"/>
          <prop k="is_repeated" v="1"/>
          <prop k="offset" v="0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" alpha="1" name="@1@0" type="fill">
            <layer pass="0" locked="0" class="SimpleFill" enabled="1">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="255,127,0,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="156,63,170,0"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.26"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" alpha="1" name="2" type="line">
        <layer pass="0" locked="0" class="ArrowLine" enabled="1">
          <prop k="arrow_start_width" v="0"/>
          <prop k="arrow_start_width_unit" v="MM"/>
          <prop k="arrow_start_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="arrow_type" v="0"/>
          <prop k="arrow_width" v="0.4"/>
          <prop k="arrow_width_unit" v="MM"/>
          <prop k="arrow_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_length" v="0.9"/>
          <prop k="head_length_unit" v="MM"/>
          <prop k="head_length_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_thickness" v="0.9"/>
          <prop k="head_thickness_unit" v="MM"/>
          <prop k="head_thickness_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_type" v="0"/>
          <prop k="is_curved" v="1"/>
          <prop k="is_repeated" v="1"/>
          <prop k="offset" v="0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" alpha="1" name="@2@0" type="fill">
            <layer pass="0" locked="0" class="SimpleFill" enabled="1">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,255,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="198,229,93,0"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.26"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" alpha="1" name="3" type="line">
        <layer pass="0" locked="0" class="SimpleLine" enabled="1">
          <prop k="capstyle" v="square"/>
          <prop k="customdash" v="5;2"/>
          <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="MM"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="line_color" v="35,35,35,255"/>
          <prop k="line_style" v="dash"/>
          <prop k="line_width" v="0.4"/>
          <prop k="line_width_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
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
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory penAlpha="255" maxScaleDenominator="1e+8" scaleBasedVisibility="0" rotationOffset="270" sizeType="MM" scaleDependency="Area" opacity="1" minimumSize="0" enabled="0" lineSizeType="MM" diagramOrientation="Up" height="15" penColor="#000000" width="15" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" barWidth="5" labelPlacementMethod="XHeight" sizeScale="3x:0,0,0,0,0,0" penWidth="0" backgroundColor="#ffffff" minScaleDenominator="0">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="2" dist="0" zIndex="0" priority="0" linePlacementFlags="18" showAll="1" obstacle="0">
    <properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <fieldConfiguration>
    <field name="col">
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
    <field name="target1col">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="target1row">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="part1">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="distance1">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="lnduSource">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="lnduTarg">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="jump">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="targetX">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="targetY">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sourceX">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="sourceY">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="col" name="" index="0"/>
    <alias field="row" name="" index="1"/>
    <alias field="target1col" name="" index="2"/>
    <alias field="target1row" name="" index="3"/>
    <alias field="part1" name="" index="4"/>
    <alias field="distance1" name="" index="5"/>
    <alias field="lnduSource" name="" index="6"/>
    <alias field="lnduTarg" name="" index="7"/>
    <alias field="jump" name="" index="8"/>
    <alias field="targetX" name="" index="9"/>
    <alias field="targetY" name="" index="10"/>
    <alias field="sourceX" name="" index="11"/>
    <alias field="sourceY" name="" index="12"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="col" applyOnUpdate="0"/>
    <default expression="" field="row" applyOnUpdate="0"/>
    <default expression="" field="target1col" applyOnUpdate="0"/>
    <default expression="" field="target1row" applyOnUpdate="0"/>
    <default expression="" field="part1" applyOnUpdate="0"/>
    <default expression="" field="distance1" applyOnUpdate="0"/>
    <default expression="" field="lnduSource" applyOnUpdate="0"/>
    <default expression="" field="lnduTarg" applyOnUpdate="0"/>
    <default expression="" field="jump" applyOnUpdate="0"/>
    <default expression="" field="targetX" applyOnUpdate="0"/>
    <default expression="" field="targetY" applyOnUpdate="0"/>
    <default expression="" field="sourceX" applyOnUpdate="0"/>
    <default expression="" field="sourceY" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" field="col" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="row" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="target1col" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="target1row" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="part1" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="distance1" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="lnduSource" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="lnduTarg" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="jump" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="targetX" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="targetY" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="sourceX" exp_strength="0" constraints="0" notnull_strength="0"/>
    <constraint unique_strength="0" field="sourceY" exp_strength="0" constraints="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="col" exp="" desc=""/>
    <constraint field="row" exp="" desc=""/>
    <constraint field="target1col" exp="" desc=""/>
    <constraint field="target1row" exp="" desc=""/>
    <constraint field="part1" exp="" desc=""/>
    <constraint field="distance1" exp="" desc=""/>
    <constraint field="lnduSource" exp="" desc=""/>
    <constraint field="lnduTarg" exp="" desc=""/>
    <constraint field="jump" exp="" desc=""/>
    <constraint field="targetX" exp="" desc=""/>
    <constraint field="targetY" exp="" desc=""/>
    <constraint field="sourceX" exp="" desc=""/>
    <constraint field="sourceY" exp="" desc=""/>
  </constraintExpressions>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="&quot;row&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" name="col" type="field" width="-1"/>
      <column hidden="0" name="row" type="field" width="-1"/>
      <column hidden="0" name="target1col" type="field" width="-1"/>
      <column hidden="0" name="target1row" type="field" width="-1"/>
      <column hidden="0" name="part1" type="field" width="-1"/>
      <column hidden="0" name="distance1" type="field" width="-1"/>
      <column hidden="0" name="jump" type="field" width="-1"/>
      <column hidden="0" name="targetX" type="field" width="-1"/>
      <column hidden="0" name="targetY" type="field" width="-1"/>
      <column hidden="0" name="sourceX" type="field" width="-1"/>
      <column hidden="0" name="sourceY" type="field" width="-1"/>
      <column hidden="1" type="actions" width="-1"/>
      <column hidden="0" name="lnduSource" type="field" width="-1"/>
      <column hidden="0" name="lnduTarg" type="field" width="-1"/>
    </columns>
  </attributetableconfig>
  <editform>.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
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
    <field name="SediOut" editable="1"/>
    <field name="col" editable="1"/>
    <field name="cum_perc" editable="1"/>
    <field name="cum_sum" editable="1"/>
    <field name="distance1" editable="1"/>
    <field name="jump" editable="1"/>
    <field name="lnduSource" editable="1"/>
    <field name="lnduTarg" editable="1"/>
    <field name="part1" editable="1"/>
    <field name="row" editable="1"/>
    <field name="sourceX" editable="1"/>
    <field name="sourceY" editable="1"/>
    <field name="target1col" editable="1"/>
    <field name="target1row" editable="1"/>
    <field name="targetX" editable="1"/>
    <field name="targetY" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="SediOut"/>
    <field labelOnTop="0" name="col"/>
    <field labelOnTop="0" name="cum_perc"/>
    <field labelOnTop="0" name="cum_sum"/>
    <field labelOnTop="0" name="distance1"/>
    <field labelOnTop="0" name="jump"/>
    <field labelOnTop="0" name="lnduSource"/>
    <field labelOnTop="0" name="lnduTarg"/>
    <field labelOnTop="0" name="part1"/>
    <field labelOnTop="0" name="row"/>
    <field labelOnTop="0" name="sourceX"/>
    <field labelOnTop="0" name="sourceY"/>
    <field labelOnTop="0" name="target1col"/>
    <field labelOnTop="0" name="target1row"/>
    <field labelOnTop="0" name="targetX"/>
    <field labelOnTop="0" name="targetY"/>
  </labelOnTop>
  <widgets/>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <expressionfields/>
  <previewExpression>COALESCE( "col", '&lt;NULL>' )</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
