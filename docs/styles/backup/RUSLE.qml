<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.13" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="0" classificationMax="20" classificationMinMaxOrigin="User" band="1" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="DISCRETE" clip="0">
          <item alpha="255" value="1" label="Verwaarloosbaar" color="#028100"/>
          <item alpha="255" value="2" label="Zeer laag" color="#12da2d"/>
          <item alpha="255" value="5" label="Laag" color="#ffff00"/>
          <item alpha="255" value="10" label="Medium" color="#ffaa00"/>
          <item alpha="255" value="20" label="Hoog" color="#ff0000"/>
          <item alpha="255" value="1500" label="Zeer Hoog" color="#a800e6"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
