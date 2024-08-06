<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" readOnly="0" labelsEnabled="0" simplifyAlgorithm="0" minScale="1e+8" version="3.2.0-Bonn" simplifyDrawingTol="1" simplifyDrawingHints="1" maxScale="0" hasScaleBasedVisibilityFlag="0" simplifyLocal="1">
  <renderer-v2 forceraster="0" symbollevels="0" enableorderby="0" type="RuleRenderer">
    <rules key="{fb2ac34d-e848-4fb8-aa0c-397728ea8fd8}">
      <rule label="zeer laag" key="{9e0cb11e-0db8-4536-bcf3-40ea49d47786}" symbol="0" filter="&quot;sedlen&quot; &lt; 50"/>
      <rule label="laag" key="{b61b4a87-8a5f-488c-98c0-15a4232a1599}" symbol="1" filter="&quot;sedlen&quot; >= 50 AND &quot;sedlen&quot; &lt; 75"/>
      <rule label="Gemiddeld" key="{2188da37-d988-45a4-9ff7-102207fc347e}" symbol="2" filter="&quot;sedlen&quot; >= 75 AND &quot;sedlen&quot; &lt; 100"/>
      <rule label="hoog" key="{4432eb8b-b85b-43c0-9fc4-7ef6ac16d7a0}" symbol="3" filter="&quot;sedlen&quot; >= 100 AND &quot;sedlen&quot; &lt; 125"/>
      <rule label="zeer hoog" key="{b45bd62a-74b4-4c15-8d0e-f07960a598c8}" symbol="4" filter="&quot;sedlen&quot; >= 125 "/>
    </rules>
    <symbols>
      <symbol name="0" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,251,255,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="105,231,20,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="2" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="230,249,57,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="3" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="255,127,0,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="4" type="line" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleLine" enabled="1" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="255,0,21,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.66" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
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
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory enabled="0" lineSizeScale="3x:0,0,0,0,0,0" minScaleDenominator="-2.14748e+9" penAlpha="255" labelPlacementMethod="XHeight" diagramOrientation="Up" height="15" penColor="#000000" lineSizeType="MM" backgroundColor="#ffffff" scaleDependency="Area" sizeScale="3x:0,0,0,0,0,0" minimumSize="0" maxScaleDenominator="1e+8" backgroundAlpha="255" rotationOffset="270" scaleBasedVisibility="0" penWidth="0" sizeType="MM" opacity="1" width="15" barWidth="5">
      <fontProperties description="MS Shell Dlg 2,7.5,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#000000" label="" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="2" showAll="1" dist="0" priority="0" placement="2" zIndex="0" obstacle="0">
    <properties>
      <Option type="Map">
        <Option name="name" value="" type="QString"/>
        <Option name="properties"/>
        <Option name="type" value="collection" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <fieldConfiguration>
    <field name="OBJECTID">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="VHAS">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="VHAG">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="PROV">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="PROV1">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="BEKNR">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="GEO">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="VHAZC">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="ENABLED">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="LOKAAL">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="GLOBALID">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="SHAPE_Leng">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="WATERL">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="NAAM">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="NAMEN">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="CATC">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="BEHE">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="WATKWAL">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="NR">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Sediment">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="len">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="sedlen">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="logsedlen">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="0" type="QString"/>
            <Option name="UseHtml" value="0" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="OBJECTID" index="0"/>
    <alias name="" field="VHAS" index="1"/>
    <alias name="" field="VHAG" index="2"/>
    <alias name="" field="PROV" index="3"/>
    <alias name="" field="PROV1" index="4"/>
    <alias name="" field="BEKNR" index="5"/>
    <alias name="" field="GEO" index="6"/>
    <alias name="" field="VHAZC" index="7"/>
    <alias name="" field="ENABLED" index="8"/>
    <alias name="" field="LOKAAL" index="9"/>
    <alias name="" field="GLOBALID" index="10"/>
    <alias name="" field="SHAPE_Leng" index="11"/>
    <alias name="" field="WATERL" index="12"/>
    <alias name="" field="NAAM" index="13"/>
    <alias name="" field="NAMEN" index="14"/>
    <alias name="" field="CATC" index="15"/>
    <alias name="" field="BEHE" index="16"/>
    <alias name="" field="WATKWAL" index="17"/>
    <alias name="" field="NR" index="18"/>
    <alias name="" field="Sediment" index="19"/>
    <alias name="" field="len" index="20"/>
    <alias name="" field="sedlen" index="21"/>
    <alias name="" field="logsedlen" index="22"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="OBJECTID" expression=""/>
    <default applyOnUpdate="0" field="VHAS" expression=""/>
    <default applyOnUpdate="0" field="VHAG" expression=""/>
    <default applyOnUpdate="0" field="PROV" expression=""/>
    <default applyOnUpdate="0" field="PROV1" expression=""/>
    <default applyOnUpdate="0" field="BEKNR" expression=""/>
    <default applyOnUpdate="0" field="GEO" expression=""/>
    <default applyOnUpdate="0" field="VHAZC" expression=""/>
    <default applyOnUpdate="0" field="ENABLED" expression=""/>
    <default applyOnUpdate="0" field="LOKAAL" expression=""/>
    <default applyOnUpdate="0" field="GLOBALID" expression=""/>
    <default applyOnUpdate="0" field="SHAPE_Leng" expression=""/>
    <default applyOnUpdate="0" field="WATERL" expression=""/>
    <default applyOnUpdate="0" field="NAAM" expression=""/>
    <default applyOnUpdate="0" field="NAMEN" expression=""/>
    <default applyOnUpdate="0" field="CATC" expression=""/>
    <default applyOnUpdate="0" field="BEHE" expression=""/>
    <default applyOnUpdate="0" field="WATKWAL" expression=""/>
    <default applyOnUpdate="0" field="NR" expression=""/>
    <default applyOnUpdate="0" field="Sediment" expression=""/>
    <default applyOnUpdate="0" field="len" expression=""/>
    <default applyOnUpdate="0" field="sedlen" expression=""/>
    <default applyOnUpdate="0" field="logsedlen" expression=""/>
  </defaults>
  <constraints>
    <constraint field="OBJECTID" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="VHAS" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="VHAG" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="PROV" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="PROV1" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="BEKNR" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="GEO" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="VHAZC" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="ENABLED" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="LOKAAL" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="GLOBALID" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="SHAPE_Leng" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="WATERL" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="NAAM" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="NAMEN" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="CATC" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="BEHE" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="WATKWAL" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="NR" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="Sediment" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="len" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="sedlen" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
    <constraint field="logsedlen" unique_strength="0" constraints="0" notnull_strength="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="OBJECTID" exp="" desc=""/>
    <constraint field="VHAS" exp="" desc=""/>
    <constraint field="VHAG" exp="" desc=""/>
    <constraint field="PROV" exp="" desc=""/>
    <constraint field="PROV1" exp="" desc=""/>
    <constraint field="BEKNR" exp="" desc=""/>
    <constraint field="GEO" exp="" desc=""/>
    <constraint field="VHAZC" exp="" desc=""/>
    <constraint field="ENABLED" exp="" desc=""/>
    <constraint field="LOKAAL" exp="" desc=""/>
    <constraint field="GLOBALID" exp="" desc=""/>
    <constraint field="SHAPE_Leng" exp="" desc=""/>
    <constraint field="WATERL" exp="" desc=""/>
    <constraint field="NAAM" exp="" desc=""/>
    <constraint field="NAMEN" exp="" desc=""/>
    <constraint field="CATC" exp="" desc=""/>
    <constraint field="BEHE" exp="" desc=""/>
    <constraint field="WATKWAL" exp="" desc=""/>
    <constraint field="NR" exp="" desc=""/>
    <constraint field="Sediment" exp="" desc=""/>
    <constraint field="len" exp="" desc=""/>
    <constraint field="sedlen" exp="" desc=""/>
    <constraint field="logsedlen" exp="" desc=""/>
  </constraintExpressions>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;logsedlen&quot;" sortOrder="1">
    <columns>
      <column hidden="0" name="OBJECTID" type="field" width="-1"/>
      <column hidden="0" name="VHAS" type="field" width="-1"/>
      <column hidden="0" name="VHAG" type="field" width="-1"/>
      <column hidden="0" name="PROV" type="field" width="-1"/>
      <column hidden="0" name="PROV1" type="field" width="-1"/>
      <column hidden="0" name="BEKNR" type="field" width="-1"/>
      <column hidden="0" name="GEO" type="field" width="-1"/>
      <column hidden="0" name="VHAZC" type="field" width="-1"/>
      <column hidden="0" name="ENABLED" type="field" width="-1"/>
      <column hidden="0" name="LOKAAL" type="field" width="-1"/>
      <column hidden="0" name="GLOBALID" type="field" width="-1"/>
      <column hidden="0" name="SHAPE_Leng" type="field" width="-1"/>
      <column hidden="0" name="WATERL" type="field" width="-1"/>
      <column hidden="0" name="NAAM" type="field" width="-1"/>
      <column hidden="0" name="NAMEN" type="field" width="-1"/>
      <column hidden="0" name="CATC" type="field" width="-1"/>
      <column hidden="0" name="BEHE" type="field" width="-1"/>
      <column hidden="0" name="WATKWAL" type="field" width="-1"/>
      <column hidden="0" name="NR" type="field" width="-1"/>
      <column hidden="0" name="Sediment" type="field" width="-1"/>
      <column hidden="0" name="len" type="field" width="-1"/>
      <column hidden="0" name="sedlen" type="field" width="108"/>
      <column hidden="1" type="actions" width="-1"/>
      <column hidden="0" name="logsedlen" type="field" width="-1"/>
    </columns>
  </attributetableconfig>
  <editform>D:/Dropbox (Fluves)/ALBON/Modelberekeningen/BELINI/2de_overleg/PostProces/Scenario2/krt</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>D:/Dropbox (Fluves)/ALBON/Modelberekeningen/BELINI/2de_overleg/PostProces/Scenario2/krt</editforminitfilepath>
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
    <field name="BEHE" editable="1"/>
    <field name="BEKNR" editable="1"/>
    <field name="CATC" editable="1"/>
    <field name="ENABLED" editable="1"/>
    <field name="GEO" editable="1"/>
    <field name="GLOBALID" editable="1"/>
    <field name="LOKAAL" editable="1"/>
    <field name="NAAM" editable="1"/>
    <field name="NAMEN" editable="1"/>
    <field name="NR" editable="1"/>
    <field name="OBJECTID" editable="1"/>
    <field name="PROV" editable="1"/>
    <field name="PROV1" editable="1"/>
    <field name="SHAPE_Leng" editable="1"/>
    <field name="Sediment" editable="1"/>
    <field name="VHAG" editable="1"/>
    <field name="VHAS" editable="1"/>
    <field name="VHAZC" editable="1"/>
    <field name="WATERL" editable="1"/>
    <field name="WATKWAL" editable="1"/>
    <field name="len" editable="1"/>
    <field name="logsedlen" editable="1"/>
    <field name="sedlen" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="BEHE" labelOnTop="0"/>
    <field name="BEKNR" labelOnTop="0"/>
    <field name="CATC" labelOnTop="0"/>
    <field name="ENABLED" labelOnTop="0"/>
    <field name="GEO" labelOnTop="0"/>
    <field name="GLOBALID" labelOnTop="0"/>
    <field name="LOKAAL" labelOnTop="0"/>
    <field name="NAAM" labelOnTop="0"/>
    <field name="NAMEN" labelOnTop="0"/>
    <field name="NR" labelOnTop="0"/>
    <field name="OBJECTID" labelOnTop="0"/>
    <field name="PROV" labelOnTop="0"/>
    <field name="PROV1" labelOnTop="0"/>
    <field name="SHAPE_Leng" labelOnTop="0"/>
    <field name="Sediment" labelOnTop="0"/>
    <field name="VHAG" labelOnTop="0"/>
    <field name="VHAS" labelOnTop="0"/>
    <field name="VHAZC" labelOnTop="0"/>
    <field name="WATERL" labelOnTop="0"/>
    <field name="WATKWAL" labelOnTop="0"/>
    <field name="len" labelOnTop="0"/>
    <field name="logsedlen" labelOnTop="0"/>
    <field name="sedlen" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <expressionfields/>
  <previewExpression>COALESCE( "NAMEN", '&lt;NULL>' )</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
