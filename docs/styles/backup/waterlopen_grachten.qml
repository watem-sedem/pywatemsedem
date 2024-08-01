<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.4.2-Madeira" simplifyAlgorithm="0" simplifyDrawingTol="1" maxScale="0" simplifyDrawingHints="1" styleCategories="AllStyleCategories" minScale="1e+08" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" labelsEnabled="0" simplifyMaxScale="1" readOnly="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="RuleRenderer" symbollevels="0" forceraster="0" enableorderby="0">
    <rules key="{c5534247-6af9-4a57-9e90-2225efe802cf}">
      <rule filter="&quot;WTRLICHC&quot; = 'G'" label="G" key="{54831936-3b45-4008-9b0e-163711c46b42}" symbol="0"/>
      <rule filter="ELSE" key="{0f354f20-f34f-4cc5-910a-8019a9f32fb8}" symbol="1"/>
    </rules>
    <symbols>
      <symbol type="line" alpha="1" name="0" clip_to_extent="1">
        <layer locked="0" enabled="1" class="SimpleLine" pass="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="18,159,169,255" k="line_color"/>
          <prop v="dash" k="line_style"/>
          <prop v="0.46" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="line" alpha="1" name="1" clip_to_extent="1">
        <layer locked="0" enabled="1" class="SimpleLine" pass="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="4,246,254,255" k="line_color"/>
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
    <property key="dualview/previewExpressions" value="OBJECTID"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory labelPlacementMethod="XHeight" rotationOffset="270" sizeType="MM" penAlpha="255" sizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" enabled="0" minimumSize="0" backgroundColor="#ffffff" penWidth="0" width="15" barWidth="5" penColor="#000000" maxScaleDenominator="1e+08" opacity="1" minScaleDenominator="0" lineSizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up" height="15" scaleDependency="Area" lineSizeType="MM" backgroundAlpha="255">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" dist="0" showAll="1" placement="2" zIndex="0" linePlacementFlags="18" priority="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="OIDN">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="UIDN">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="VHAS">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="VHAG">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="NAAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="REGCODE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="REGCODE1">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BEHEER">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="CATC">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LBLCATC">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BEKNR">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BEKNAAM">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="STRMGEB">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="KWALDOEL">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LBLKWAL">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="GEO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LBLGEO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="VHAZONENR">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="WTRLICHC">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LENGTE">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="OIDN" name=""/>
    <alias index="1" field="UIDN" name=""/>
    <alias index="2" field="VHAS" name=""/>
    <alias index="3" field="VHAG" name=""/>
    <alias index="4" field="NAAM" name=""/>
    <alias index="5" field="REGCODE" name=""/>
    <alias index="6" field="REGCODE1" name=""/>
    <alias index="7" field="BEHEER" name=""/>
    <alias index="8" field="CATC" name=""/>
    <alias index="9" field="LBLCATC" name=""/>
    <alias index="10" field="BEKNR" name=""/>
    <alias index="11" field="BEKNAAM" name=""/>
    <alias index="12" field="STRMGEB" name=""/>
    <alias index="13" field="KWALDOEL" name=""/>
    <alias index="14" field="LBLKWAL" name=""/>
    <alias index="15" field="GEO" name=""/>
    <alias index="16" field="LBLGEO" name=""/>
    <alias index="17" field="VHAZONENR" name=""/>
    <alias index="18" field="WTRLICHC" name=""/>
    <alias index="19" field="LENGTE" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" field="OIDN" applyOnUpdate="0"/>
    <default expression="" field="UIDN" applyOnUpdate="0"/>
    <default expression="" field="VHAS" applyOnUpdate="0"/>
    <default expression="" field="VHAG" applyOnUpdate="0"/>
    <default expression="" field="NAAM" applyOnUpdate="0"/>
    <default expression="" field="REGCODE" applyOnUpdate="0"/>
    <default expression="" field="REGCODE1" applyOnUpdate="0"/>
    <default expression="" field="BEHEER" applyOnUpdate="0"/>
    <default expression="" field="CATC" applyOnUpdate="0"/>
    <default expression="" field="LBLCATC" applyOnUpdate="0"/>
    <default expression="" field="BEKNR" applyOnUpdate="0"/>
    <default expression="" field="BEKNAAM" applyOnUpdate="0"/>
    <default expression="" field="STRMGEB" applyOnUpdate="0"/>
    <default expression="" field="KWALDOEL" applyOnUpdate="0"/>
    <default expression="" field="LBLKWAL" applyOnUpdate="0"/>
    <default expression="" field="GEO" applyOnUpdate="0"/>
    <default expression="" field="LBLGEO" applyOnUpdate="0"/>
    <default expression="" field="VHAZONENR" applyOnUpdate="0"/>
    <default expression="" field="WTRLICHC" applyOnUpdate="0"/>
    <default expression="" field="LENGTE" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" field="OIDN" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="UIDN" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="VHAS" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="VHAG" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="NAAM" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="REGCODE" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="REGCODE1" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="BEHEER" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="CATC" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="LBLCATC" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="BEKNR" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="BEKNAAM" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="STRMGEB" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="KWALDOEL" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="LBLKWAL" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="GEO" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="LBLGEO" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="VHAZONENR" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="WTRLICHC" notnull_strength="0" unique_strength="0" constraints="0"/>
    <constraint exp_strength="0" field="LENGTE" notnull_strength="0" unique_strength="0" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="OIDN" exp=""/>
    <constraint desc="" field="UIDN" exp=""/>
    <constraint desc="" field="VHAS" exp=""/>
    <constraint desc="" field="VHAG" exp=""/>
    <constraint desc="" field="NAAM" exp=""/>
    <constraint desc="" field="REGCODE" exp=""/>
    <constraint desc="" field="REGCODE1" exp=""/>
    <constraint desc="" field="BEHEER" exp=""/>
    <constraint desc="" field="CATC" exp=""/>
    <constraint desc="" field="LBLCATC" exp=""/>
    <constraint desc="" field="BEKNR" exp=""/>
    <constraint desc="" field="BEKNAAM" exp=""/>
    <constraint desc="" field="STRMGEB" exp=""/>
    <constraint desc="" field="KWALDOEL" exp=""/>
    <constraint desc="" field="LBLKWAL" exp=""/>
    <constraint desc="" field="GEO" exp=""/>
    <constraint desc="" field="LBLGEO" exp=""/>
    <constraint desc="" field="VHAZONENR" exp=""/>
    <constraint desc="" field="WTRLICHC" exp=""/>
    <constraint desc="" field="LENGTE" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" type="field" name="VHAS" width="-1"/>
      <column hidden="0" type="field" name="VHAG" width="-1"/>
      <column hidden="0" type="field" name="BEKNR" width="-1"/>
      <column hidden="0" type="field" name="GEO" width="-1"/>
      <column hidden="0" type="field" name="NAAM" width="-1"/>
      <column hidden="0" type="field" name="CATC" width="-1"/>
      <column hidden="1" type="actions" width="-1"/>
      <column hidden="0" type="field" name="OIDN" width="-1"/>
      <column hidden="0" type="field" name="UIDN" width="-1"/>
      <column hidden="0" type="field" name="REGCODE" width="-1"/>
      <column hidden="0" type="field" name="REGCODE1" width="-1"/>
      <column hidden="0" type="field" name="BEHEER" width="-1"/>
      <column hidden="0" type="field" name="LBLCATC" width="-1"/>
      <column hidden="0" type="field" name="BEKNAAM" width="-1"/>
      <column hidden="0" type="field" name="STRMGEB" width="-1"/>
      <column hidden="0" type="field" name="KWALDOEL" width="-1"/>
      <column hidden="0" type="field" name="LBLKWAL" width="-1"/>
      <column hidden="0" type="field" name="LBLGEO" width="-1"/>
      <column hidden="0" type="field" name="VHAZONENR" width="-1"/>
      <column hidden="0" type="field" name="WTRLICHC" width="-1"/>
      <column hidden="0" type="field" name="LENGTE" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1">C:/GIS/Projecten</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>C:/GIS/Projecten</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
Formulieren van QGIS kunnen een functie voor Python hebben die wordt aangeroepen wanneer het formulier wordt geopend.

Gebruik deze functie om extra logica aan uw formulieren toe te voegen.

Voer de naam van de functie in in het veld "Python Init function".

Een voorbeeld volgt hieronder:
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
    <field name="BEHEER" editable="1"/>
    <field name="BEKNAAM" editable="1"/>
    <field name="BEKNR" editable="1"/>
    <field name="CATC" editable="1"/>
    <field name="ENABLED" editable="1"/>
    <field name="GEO" editable="1"/>
    <field name="GLOBALID" editable="1"/>
    <field name="KWALDOEL" editable="1"/>
    <field name="LBLCATC" editable="1"/>
    <field name="LBLGEO" editable="1"/>
    <field name="LBLKWAL" editable="1"/>
    <field name="LENGTE" editable="1"/>
    <field name="LOKAAL" editable="1"/>
    <field name="NAAM" editable="1"/>
    <field name="NAMEN" editable="1"/>
    <field name="NR" editable="1"/>
    <field name="OBJECTID" editable="1"/>
    <field name="OIDN" editable="1"/>
    <field name="PROV" editable="1"/>
    <field name="PROV1" editable="1"/>
    <field name="REGCODE" editable="1"/>
    <field name="REGCODE1" editable="1"/>
    <field name="SHAPE_Leng" editable="1"/>
    <field name="STRMGEB" editable="1"/>
    <field name="UIDN" editable="1"/>
    <field name="VHAG" editable="1"/>
    <field name="VHAS" editable="1"/>
    <field name="VHAZC" editable="1"/>
    <field name="VHAZONENR" editable="1"/>
    <field name="WATERL" editable="1"/>
    <field name="WATKWAL" editable="1"/>
    <field name="WTRLICHC" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="BEHE" labelOnTop="0"/>
    <field name="BEHEER" labelOnTop="0"/>
    <field name="BEKNAAM" labelOnTop="0"/>
    <field name="BEKNR" labelOnTop="0"/>
    <field name="CATC" labelOnTop="0"/>
    <field name="ENABLED" labelOnTop="0"/>
    <field name="GEO" labelOnTop="0"/>
    <field name="GLOBALID" labelOnTop="0"/>
    <field name="KWALDOEL" labelOnTop="0"/>
    <field name="LBLCATC" labelOnTop="0"/>
    <field name="LBLGEO" labelOnTop="0"/>
    <field name="LBLKWAL" labelOnTop="0"/>
    <field name="LENGTE" labelOnTop="0"/>
    <field name="LOKAAL" labelOnTop="0"/>
    <field name="NAAM" labelOnTop="0"/>
    <field name="NAMEN" labelOnTop="0"/>
    <field name="NR" labelOnTop="0"/>
    <field name="OBJECTID" labelOnTop="0"/>
    <field name="OIDN" labelOnTop="0"/>
    <field name="PROV" labelOnTop="0"/>
    <field name="PROV1" labelOnTop="0"/>
    <field name="REGCODE" labelOnTop="0"/>
    <field name="REGCODE1" labelOnTop="0"/>
    <field name="SHAPE_Leng" labelOnTop="0"/>
    <field name="STRMGEB" labelOnTop="0"/>
    <field name="UIDN" labelOnTop="0"/>
    <field name="VHAG" labelOnTop="0"/>
    <field name="VHAS" labelOnTop="0"/>
    <field name="VHAZC" labelOnTop="0"/>
    <field name="VHAZONENR" labelOnTop="0"/>
    <field name="WATERL" labelOnTop="0"/>
    <field name="WATKWAL" labelOnTop="0"/>
    <field name="WTRLICHC" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>OBJECTID</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
