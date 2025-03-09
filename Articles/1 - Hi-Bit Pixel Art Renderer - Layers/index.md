#Writing a Hi-Bit Pixel Art Renderer - Layers

This is the first in a series of articles covering the development of my hi-bit pixel art renderer. By hi-bit I mean a 2D rendering system with a retro, pixel art aesthetic but doesn't constrain itself to the limitations of retro hardware. This is in contrast to games like Shovel Knight that aim to adhere to the limitations of a specific platform. Hi-bit games will often use rendering techniques and features that wouldn't have been possible on older hardware.

Note: The renderer was built using C++ and OpenGL, but the techniques I discuss here should apply to any API or engine you are using.

<figure>
    <img title="" src="assets/omega.png" alt="" data-align="center">
  	<figcaption><small>Figure 1 - Omega by pieceoftoast</small></figcaption>
</figure>

This image was created by Deviant Art user [pieceoftoast](https://www.deviantart.com/pieceoftoast). This is an art piece, not a screenshot from a game. I liked how this image evoked older games like those made by Sierra On-Line and Lucas Arts but also had a modern, updated feel to it. During game development, artists sometimes create images like this to illustrate how all the rendering features should look in the final game. We called these "game in a frame" concepts. To me, this image seemed like the perfect "game in a frame" to start development on my hi-bit renderer. 

My first step was to identify all the rendering features from the concept image that I'd need to implement.

<figure>
    <img title="" src="assets/features.png" alt="" data-align="center">
  	<figcaption><small>Figure 2 - Features for replicating this image in my hi-bit Renderer</small></figcaption>
</figure>

Here's what I came up with:

- Arbitrary number of layers. I counted at least 8 layers in the scene. Some layers should have parallax with respect to each other. For other sets of layers, we will not want them to parallax.
- Consistent texel size. Texels are always the same size on screen. 
- Normal-mapped dynamic lighting. Look at the wall edges near the glowing signs and notice how they are lit up.
- Dynamic shadows
- Glowing textures
- Lens flares

I also knew that I wanted my renderer to implement pixel-perfect texture sampling. This means that screen pixels that overlap multiple texels (from the same tile or adjacent tiles) should perfectly blend the percentage contribution from each texel. 

I'll discuss the implementation of each of these features in future articles. For the remainder of this article, I'll explain how I supported layers in the renderer.

###Approach 1 - 2D Orthographic layers
My initial approach was to copy how 2D games did it before the advent of 3D rendering: Represent the scene as a series of 2D layers and assign each layer a parallax scalar. Each layer contained tiles. Tiles are just screen-facing quads with a texture applied to them. At render time, I drew the layers back-to-front using an orthographic view-projection matrix. When calculating the view matrix for a layer, I'd scale the translation by the parallax amount. So for a layer with a parallax scalar equal to 1, the layer would track the camera exactly. For a layer with a parallax scalar set to .5, the tiles in that layer would move at half the speed. 

<figure>
    <img title="" src="assets/LayerDiagram.jpg" alt="" data-align="center" width="700">
  	<figcaption><small>Figure 3 - Orthographic layers combined for the final image. The orange square is the orthographic camera bounds for that layer.</small></figcaption>
</figure>

This approach quickly proved cumbersome. Scene management, such as selecting and moving tiles, was complicated by the presence of layers. Moving a tile farther back in the scene required moving the tile to another layer. If that layer didn't have the parallax amount I wanted, I'd have to create another layer. For a game with just a few layers, this approach could be managable. But if I wanted more than a few then I needed a different approach.

###Approach 2 - 3D perspective with scaled tiles
For my next approach, I extended the renderer to 3D. I removed the concept of layers and instead gave each tile a z coordinate. The scene was rendered using a perspective projection matrix which gave the desired parallax effect when the camera moved in the xy plane. But by using a perspective projection, tiles farther in the background were drawn smaller on the screen. This broke the goal of having a consistent texel size. To fix this, I calculated an xy scale for each tile depending on its distance from the camera. The farther a tile was from the camera, the more it would need to be scaled up to offset the size reduction caused by perspective.

<figure>
    <img title="" src="assets/ScaledPerspectiveDiagram.jpg" alt="" data-align="center" width="700">
  	<figcaption><small>Figure 4 - Tiles scaled to maintain consistent texel size</small></figcaption>
</figure>

I picked z==0 as the location at which the tile's scale would equal 1. Here is how I calculated the camera distance:

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

I kept gCameraDist constant, the camera could move in x and y but was fixed in z. Moving in z would cause closer tiles to scale up/down faster than tiles farther away. This would break the consistent texel size goal. When placing a new tile or changing a tiles z coordinate, I'd calculate the new tile scale by calling the function GetTexelScaleAtZ. 

This technique worked well and I was mostly satisfied with it. There was a bit of code complexity in managing the tile scale (moving multiple tiles at different z-depths was a tricky problem to get right). However, I proceeded with development using this approach for quite a while. It wasn't until I began implementing shadows that I started to rethink it. The problem was that if we did a parallel projection of a shadow onto a tile farther in the distance, the shadow texels were smaller than the texels of the tile they were projected onto. I could have used nearest sampling to make them the correct size, but then we'd be downsampling our pixel art shadow. I wanted to avoid downsampled shadows because downsampling ruins the look of pixel art (for example: single-texel lines will disappear).

###Approach 3 - 3D Orthographic Skewed

To make the shadows look good, I knew I needed to go back to using an orthographic projection with no tile scaling. But with a standard orthographic projection, there is no parallax. Objects in the background will move at the same speed as ones in the foreground. I realized I could get parallax by applying a skew transformation to the view matrix. The skew transformation would translate tiles in the x&y direction proportional to their z position in view space. 

<figure>
    <img title="" src="assets/SkewedOrthographicDiagram.jpg" alt="" data-align="center" width="500">
  	<figcaption><small>Figure 5</small></figcaption>
</figure>

Here's how I did it:

- Pick a distant world position that the camera will always be pointed at. We'll call this the vanishing point. This point should be far plane distance from the camera.
- In my case, the camera moves in the plane z==0 and the vanishing point is at (0,0,-farPlaneDistance).
- Given the world object that the camera is tracking, calculate the camera's xy position such that a line goes from the camera position, through the object we are tracking to the vanishing point. 
- With this camera position we can compute a standard non-skewed orthographic view matrix.
- Next construct a skew matrix that skews the world in the direction of the vector from the camera position to the vanishing point.
- Construct a final view matrix by multiplying the view matrix by the skew matrix. Make sure to get the multiplication order correct so that objects are first transformed into view space and then skewed. The order will depend on the conventions of your math library.

Now as the camera moves in the xy plane, tiles at different depths will parallax with each other. Tiles placed at the vanishing point distance (on the far plane) will be stationary on-screen. Tiles close to the near-plane will move the most. Tiles halfway between the near plane and far plane will move half the distance of tiles at the near plane.

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

	Vector3 vanishingPoint( 0.f, 0.f, farPlaneZ );
	Vector3 vanishingPointToCameraPos = *cameraPos - vanishingPoint;

	Matrix4 cameraPosToSkew;
	{
		float skewX = vanishingPointToCameraPos.x/vanishingPointToCameraPos.z;
		float skewY = vanishingPointToCameraPos.y/vanishingPointToCameraPos.z;
		SetIdentityMatrix( &cameraPosToSkew );
		cameraPosToSkew.m31 = -skewX;
		cameraPosToSkew.m32 = -skewY;
	}

	MultMatrices( skewedViewMat, &worldToCameraPos, &cameraPosToSkew );
}
```
Besides solving the shadowing problems, this solution had some other nice benefits:

- The code was greatly simplified by the removal of all the tile scaling code.
- I could place objects at arbitrary "layers" by changing their z coordinate.
- Tiles at the far plane never move. With my previous approach, even if I moved a tile to the far plane, it would still shift a bit. To achieve no movement with a perspective camera would have required some special case code similar to a skybox in a 3D game.

Something cool I discovered was that a skew matrix allows you to have parallax in a single axis only. For instance, you could have a game where there is parallax when the camera moves in the x direction but not in the y direction. You'd just need to change your skew matrix construction so that the infinity point always has the same y coordinate as the camera. This is something I'd like to experiment with in the future.






<!---
<video autoplay loop muted playsinline>
  <source src="assets/omega.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
-->

