<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.19" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" classificationMax="100" classificationMinMaxOrigin="User" band="1" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="DISCRETE" clip="0">
          <item alpha="255" value="0" label="No snow" color="#d6d2d0"/>
          <item alpha="255" value="20" label="0 - 20" color="#f0f9e8"/>
          <item alpha="255" value="40" label="20 - 40" color="#bae4bc"/>
          <item alpha="255" value="60" label="40 - 60" color="#7bccc4"/>
          <item alpha="255" value="80" label="60 - 80" color="#43a2ca"/>
          <item alpha="255" value="100" label="80 - 100" color="#0868ac"/>
          <item alpha="255" value="205" label="Cloud" color="#ffffff"/>
          <item alpha="255" value="inf" label="No data" color="#000000"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
