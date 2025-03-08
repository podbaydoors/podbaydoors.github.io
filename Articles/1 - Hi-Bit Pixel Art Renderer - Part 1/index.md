#Writing a Hi-Bit Pixel Art Renderer - Part 1

In this series of articles, I'm going to cover the development of my hi-bit pixel art renderer. By hi-bit I mean a 2D rendering system that has a retro, pixel art aesthetic but doesn't constrain itself to the limitations of retro hardware. This is in contrast to games like Shovel Knight that aim to adhere to the limitations of a specific platform. Hi-bit games will often use rendering techniques and features that wouldn't have been possible on older hardware.

The renderer was built using C++ and OpenGL, but the techniques I discuss here should be usable using any API or 3rd party engine.

<figure>
    <img title="" src="assets/omega.png" alt="" data-align="center">
  	<figcaption><small>Figure 1 - Omega by pieceoftoast</small></figcaption>
</figure>

This image was created by [Deviant Art user pieceoftoast](https://www.deviantart.com/pieceoftoast). This is an art piece, not a screenshot from a game. I really liked how this image evoked older games like those made by Sierra On-Line or Lucas Arts but also had a modern feel to it. During game development, artists sometimes create images like this to illustrate how all the rendering features should look in the final game. We called these "game in a frame" concepts. To me, this image seemed like the perfect "game in a frame" to start development on my hi-bit renderer. 

My first step was to identify all the rendering features from the concept image that I'd need to implement.

<figure>
    <img title="" src="assets/features.png" alt="" data-align="center">
  	<figcaption><small>Figure 2 - Features for replicating this image in my hi-bit Renderer</small></figcaption>
</figure>

Here's what I came up with:

- Consistent texel size. Texels are always the same size on screen. 
- Arbitrary number of layers. I counted at least 8 layers in the scene. Some layers should have parallax with respect to each other. For other sets of layers, we will not want them to parallax.
- Normal mapped dynamic lighting. Look at the wall edges near the glowing signs and notice how they are lit up.
- Dynamic cast shadows
- Glowing textures
- Lens flares

I also added a goal that wasn't necessarily informed by the concept image. Pixel-perfect texture sampling. Screen pixels that overlap multiple texels (from the same tile or adjacent tiles) should perfectly blend the percentage contribution from each texel.

The scene would be composed of tiles. Tiles are just screen facing quads with a texture applied to them. The first thing I needed to figure out was how to lay out tiles in the scene.

###Approach 1 - 2D Orthographic layers
My initial approach was to copy how 2D games did it before the advent of 3D rendering: Represent the scene as a series of 2D layers and assign each layer a parallax scalar. Tiles were then assigned to layers. At render time, I drew the layers back-to-front using an orthographic view-projection matrix. When calculating the view matrix for a layer, I'd scale the translation by the parallax amount. So for a layer with a parallax scalar equal to 1, the layer would track the camera exactly. For a layer with a parallax scalar set to .5, the tiles in that layer would move at half the speed. 

<figure>
    <img title="" src="assets/LayerDiagram.jpg" alt="" data-align="center" width="700">
  	<figcaption><small>Figure 3 - Orthographic layers combined for final image. Orange square is orthographic camera bounds for that layer.</small></figcaption>
</figure>

This approach quickly proved limiting and cumbersome. Scene management, such as selecting and moving tiles, was complicated by the presence of scene layers. Moving a tile farther back in the scene required moving the tile to another layer. If that layer didn't have the parallax amount I wanted, I'd have to create another layer. I realized that if I wanted more than a few layers in the scene then I needed a different approach.

###Approach 2 - 3D perspective with scaled tiles
For my next approach, I extended the renderer to 3D. I removed the concept of layers and instead gave each tile a z coordinate. The scene was rendered using a perspective projection matrix which gave the desired parallax effect when the camera moved in the xy plane. But by using a perspective projection, tiles farther in the background were drawn smaller on screen. This broke the goal of having a consistent texel size. To fix this, I calculated an xy scale for each tile depending on its distance from the camera. The farther a tile was from the camera, the more it would need to be scaled up to offset the reduction in size caused by perspective.

<figure>
    <img title="" src="assets/ScaledPerspectiveDiagram.jpg" alt="" data-align="center" width="700">
  	<figcaption><small>Figure 4 - Tiles scaled to maintain consistent texel size</small></figcaption>
</figure>

I picked z==0 as the location at which the tile's scale would equal 1. Here is how I calculated the camera distance.

```cpp
//Code that runs at renderer startup
//Set camera distance so that the height of xy plane at z==0 is gScreenHeightInTexels.
gCameraDist = (gScreenHeightInTexels)/(2.f*tanf(DegToRad(.5f*gRenderVerticalFOVDegrees)));

//Returns how much to scale a tile so that texels are a consistent on-screen size. 
float GetTexelScaleAtZ( float z )
{
	float scale = (gCameraDist-z)/gCameraDist;
	return scale;
}
```

I kept gCameraDist constant, the camera could move in x and y but was fixed in z. Moving in z would cause closer tiles to scale up/down faster than tiles farther away. This would break the consistent texel size goal. Then, when placing or moving a tile, I'd set the scale by calling the function GetTexelScaleAtZ. 

This technique worked well and I was mostly satisfied with it. There was a bit of code complexity in managing tile scale (moving multiple tiles at different z-depths was a tricky problem to get right). However, I proceeded with development using this approach for quite a while. It wasn't until I began implementing shadows that I started to rethink it. The problem was that if we did a parallel projection of a shadow onto a tile farther in the distance, the shadow texels were smaller than the texels of the tile they were projected onto. We could use nearest sampling to make them the correct size, but then we'd be downsampling our pixel art shadow. I really wanted to avoid downsampled shadows because downsampling ruins the look of pixel art.

###Approach 3 - 3D Orthographic Skewed

To make the shadows look good I knew I needed to go back to using an orthographic projection with no tile scaling. But with a standard orthographic projection there is no parallax. I then realized I could get parallax by applying a skew transformation to the view matrix. The skew transformation would translate tiles in the x&y direction proportional to their z position in view space. 

<figure>
    <img title="" src="assets/SkewedOrthographicDiagram.jpg" alt="" data-align="center" width="700">
  	<figcaption><small>Figure 5</small></figcaption>
</figure>

Here's how I did it:

- Pick a distant world position that the camera will always look at. Say (0,0,-1000) for example. Let's call this the vanishing point. 
- Given the world object that the camera is tracking, calculate a camera position such that a line goes from the camera position, through the object we are tracking to the vanishing point. 
- With this camera position we can compute a standard orthographic view matrix.
- Next construct a skew matrix that skews the frustum in the direction of the vector from the camera position to the vanishing point.
- Construct a final view matrix my multiplying the view matrix by the skew matrix. Make sure to get the multiplication order correct so that objects are first transformed into view space and then skewed. The order will depend on the conventions of your math library.

Tiles placed at the vanishing point distance (the far plane) will never move with the camera. Tiles close to the near plane will move the most. Tiles halfway between the near plane and far plane will move half the distance of tiles at the near plane.

```cpp
void MakeSkewedViewMat( Matrix4* skewedViewMat, const Vector3* cameraPos, float farPlaneZ )
{
	//2 matrices:
	//transform world space into view space centered at camera pos looking down -z
	//skew world in the direction of 0,0,farPlaneZ
	Matrix4 worldToCameraPos;
	{
		Matrix4 cameraPosToWorld;
		SetIdentityMatrix( &cameraPosToWorld );
		SetMatrixTranslation( &cameraPosToWorld, cameraPos );
		InvertRotTransMatrix( &worldToCameraPos, &cameraPosToWorld );
	}

	Vector3 infinity( 0.f, 0.f, farPlaneZ );
	Vector3 infinityToCameraPos = *cameraPos - infinity;

	Matrix4 cameraPosToSkew;
	{
		float skewX = infinityToCameraPos.x/infinityToCameraPos.z;
		float skewY = infinityToCameraPos.y/infinityToCameraPos.z;
		SetIdentityMatrix( &cameraPosToSkew );
		cameraPosToSkew.m31 = -skewX;
		cameraPosToSkew.m32 = -skewY;
	}

	MultMatrices( skewedViewMat, &worldToCameraPos, &cameraPosToSkew );
}
```
Besides solving the shadowing prolems, this solution had some other nice benefits:

- The code was greatly simplified by the removal of all the tile scaling code.
- I could place objects at arbitrary "layers" by changing its z cooridate.
- Tiles at the far plane never move. With my previous approach, even if I moved a tile to the far plane, it would still shift a bit. To achieve no movement with a perpective camera would have required some special case code similar to a skybox in a 3D game.

One of the coolest features that I discovered after implementing this that using a skew matrix allows you to have parallax in a single axis only. For instance, say you have a game where you want objects to parallax when the camera moves in x but not in y. You'd just need to change you skew matrix construction so that the infinity point always has the same y coordinate as the camera. 



<!---
<video autoplay loop muted playsinline>
  <source src="assets/omega.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
-->

