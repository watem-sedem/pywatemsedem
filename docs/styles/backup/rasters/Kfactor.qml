<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" minScale="1e+08" styleCategories="AllStyleCategories" maxScale="0" version="3.4.4-Madeira">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer alphaBand="-1" band="1" type="paletted" opacity="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry label="12" alpha="255" value="12" color="#e41a1c"/>
        <paletteEntry label="20" alpha="255" value="20" color="#377eb8"/>
        <paletteEntry label="23" alpha="255" value="23" color="#4daf4a"/>
        <paletteEntry label="25" alpha="255" value="25" color="#984ea3"/>
        <paletteEntry label="28" alpha="255" value="28" color="#ff7f00"/>
        <paletteEntry label="34" alpha="255" value="34" color="#ffff33"/>
        <paletteEntry label="40" alpha="255" value="40" color="#a65628"/>
        <paletteEntry label="41" alpha="255" value="41" color="#f781bf"/>
        <paletteEntry label="42" alpha="255" value="42" color="#999999"/>
      </colorPalette>
      <colorramp name="[source]" type="gradient">
        <prop k="color1" v="215,25,28,255"/>
        <prop k="color2" v="43,131,186,255"/>
        <prop k="discrete" v="0"/>
        <prop k="rampType" v="gradient"/>
        <prop k="stops" v="0.25;253,174,97,255:0.5;255,255,191,255:0.75;171,221,164,255"/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation colorizeRed="255" colorizeOn="0" colorizeGreen="128" grayscaleMode="0" colorizeBlue="128" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
