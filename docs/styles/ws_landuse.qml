<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" maxScale="0" version="3.16.16-Hannover" minScale="1e+08" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal fetchMode="0" mode="0" enabled="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour" enabled="false"/>
    </provider>
    <rasterrenderer alphaBand="-1" band="1" opacity="1" classificationMin="-6" type="singlebandpseudocolor" classificationMax="1" nodataColor="">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader minimumValue="-6" colorRampType="INTERPOLATED" classificationMode="1" clip="0" maximumValue="1" labelPrecision="0">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="215,25,28,255"/>
            <prop k="color2" v="43,131,186,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;253,174,97,255:0.5;255,255,191,255:0.75;171,221,164,255"/>
          </colorramp>
          <item label="Grasstrook" alpha="255" value="-6" color="#94ff00"/>
          <item label="Wateroppervlak" alpha="255" value="-5" color="#3b7db4"/>
          <item label="Grasland" alpha="255" value="-4" color="#71b651"/>
          <item label="Bos" alpha="255" value="-3" color="#387b00"/>
          <item label="Infrastructuur" alpha="255" value="-2" color="#323232"/>
          <item label="Waterloop" alpha="255" value="-1" color="#00bfff"/>
          <item label="0" alpha="0" value="0" color="#ff00ff"/>
          <item label="Akkerland" alpha="255" value="1" color="#a57132"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="13" gamma="1"/>
    <huesaturation colorizeRed="255" grayscaleMode="0" colorizeGreen="128" colorizeStrength="100" saturation="0" colorizeBlue="128" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
