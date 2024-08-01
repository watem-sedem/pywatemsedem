!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.4.4-Madeira" styleCategories="AllStyleCategories" minScale="1e+08" simplifyDrawingHints="1" simplifyMaxScale="1" simplifyDrawingTol="1" simplifyAlgorithm="0" maxScale="0" labelsEnabled="1" hasScaleBasedVisibilityFlag="0" readOnly="0" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
    <rules key="{cbdeb2f8-a64a-4438-8674-bfc86b3572a2}">
      <rule filter=" &quot;ELEV&quot; %2=0" key="{17625ef5-ad6e-42c7-8b2c-c0abc6ec922b}" symbol="0"/>
    </rules>
    <symbols>
      <symbol alpha="1" clip_to_extent="1" name="0" force_rhr="0" type="line">
        <layer locked="0" class="SimpleLine" pass="0" enabled="1">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0,0,255" k="line_color"/>
          <prop v="dash" k="line_style"/>
          <prop v="0" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="ring_filter"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
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
  <labeling type="simple">
    <settings>
      <text-style fontSizeUnit="Point" fontWeight="50" fontStrikeout="0" isExpression="0" blendMode="0" fontSize="10" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontLetterSpacing="0" multilineHeight="1" fontCapitals="0" namedStyle="Standaard" useSubstitutions="0" fontItalic="0" textColor="0,0,0,255" fontWordSpacing="0" fontUnderline="0" textOpacity="1" previewBkgrdColor="#ffffff" fieldName="ELEV" fontFamily="MS Shell Dlg 2">
        <text-buffer bufferNoFill="1" bufferJoinStyle="128" bufferDraw="0" bufferSize="1" bufferSizeUnits="MM" bufferColor="255,255,255,255" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferOpacity="1" bufferBlendMode="0"/>
        <background shapeOpacity="1" shapeSizeType="0" shapeBorderColor="128,128,128,255" shapeJoinStyle="64" shapeOffsetX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiX="0" shapeSizeUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeFillColor="255,255,255,255" shapeBlendMode="0" shapeSVGFile="" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="MM" shapeSizeY="0" shapeSizeX="0" shapeType="0" shapeRotation="0" shapeRotationType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeDraw="0" shapeOffsetUnit="MM" shapeBorderWidth="0" shapeBorderWidthUnit="MM"/>
        <shadow shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowRadiusUnit="MM" shadowOpacity="0.7" shadowRadius="1.5" shadowOffsetUnit="MM" shadowBlendMode="6" shadowUnder="0" shadowRadiusAlphaOnly="0" shadowOffsetAngle="135" shadowScale="100" shadowDraw="0" shadowColor="0,0,0,255" shadowOffsetGlobal="1"/>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" plussign="0" reverseDirectionSymbol="0" formatNumbers="0" decimals="3" placeDirectionSymbol="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" multilineAlign="4294967295" autoWrapLength="0"/>
      <placement xOffset="0" distMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" centroidWhole="0" priority="5" offsetUnits="MM" repeatDistance="0" yOffset="0" offsetType="0" placement="2" maxCurvedCharAngleOut="-25" rotationAngle="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" centroidInside="0" dist="0" distUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" maxCurvedCharAngleIn="25" preserveRotation="1" repeatDistanceUnits="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" fitInPolygonOnly="0"/>
      <rendering fontLimitPixelSize="0" mergeLines="0" fontMinPixelSize="3" minFeatureSize="0" displayAll="0" scaleMin="0" maxNumLabels="2000" limitNumLabels="0" drawLabels="1" zIndex="0" obstacleFactor="1" obstacleType="0" upsidedownLabels="0" labelPerPart="0" scaleVisibility="1" fontMaxPixelSize="10000" scaleMax="15000" obstacle="1"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties"/>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory minScaleDenominator="0" sizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" backgroundColor="#ffffff" rotationOffset="270" height="15" penAlpha="255" barWidth="5" maxScaleDenominator="1e+08" labelPlacementMethod="XHeight" minimumSize="0" sizeType="MM" lineSizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" diagramOrientation="Up" width="15" penColor="#000000" enabled="0" lineSizeType="MM" opacity="1" penWidth="0" scaleDependency="Area">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings zIndex="0" priority="0" showAll="1" linePlacementFlags="18" obstacle="0" placement="2" dist="0">
    <properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="ID">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ELEV">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="ID"/>
    <alias index="1" name="" field="ELEV"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="ID"/>
    <default expression="" applyOnUpdate="0" field="ELEV"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" exp_strength="0" constraints="0" unique_strength="0" field="ID"/>
    <constraint notnull_strength="0" exp_strength="0" constraints="0" unique_strength="0" field="ELEV"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="ID"/>
    <constraint desc="" exp="" field="ELEV"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="">
    <columns>
      <column name="ID" hidden="0" width="-1" type="field"/>
      <column name="ELEV" hidden="0" width="-1" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
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
    <field name="ELEV" editable="1"/>
    <field name="ID" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="ELEV"/>
    <field labelOnTop="0" name="ID"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>ID</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
