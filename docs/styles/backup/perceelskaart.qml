<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.14" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="0" classificationMax="1" classificationMinMaxOrigin="User" band="1" classificationMin="-6" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0">
          <item alpha="255" value="-6" label="Grasstroken" color="#ffff00"/>
          <item alpha="255" value="-5" label="Poelen/vijvers" color="#3d0ceb"/>
          <item alpha="255" value="-4" label="Weide" color="#00ff2d"/>
          <item alpha="255" value="-3" label="Bos" color="#387b00"/>
          <item alpha="255" value="-2" label="Infrastructuur" color="#000000"/>
          <item alpha="255" value="-1" label="Rivier" color="#00bfff"/>
          <item alpha="255" value="1" label="Landbouwgebied" color="#ff0000"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
