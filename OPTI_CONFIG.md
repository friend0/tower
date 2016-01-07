Configuring the Motive Capture Environment
====================================

Motive is the server application that we use to interface with the Optitrack hardware.  From these sensors (cameras), Motive puts together a point cloud of data, and triangulates the position of reflective markers in the capture volume. This allows us to determine the location,  x,  y,  z in meters, and the orientation in meters. Since our data is sampled at ~120Hz, it is clear that we can use this information to estimate velocity and acceleration of the rigid body as well.

> **Note:**

> - The HSL is outfitted with 8 Flex13 cameras
> - The system is capable of 120Hz frame-rate, or 8ms between frames

Getting Started
---------------

The system level overview is as follows:

* Motive captures point cloud data and sends information about the location and status of rigid bodies over UDP. 
*  We gather this data using a socket server in Python. In particular, this is done with Optirx. 
* This data is piped out over LAN using ZMQ. By doing this, we can retrieve feedback from the Optitrack on machines other than the one running the Motive server. 


-----

#### Starting The Cameras
We start the cameras through Optitrack's server-side tracking application, *Motive.*
- [ ] Link to Motive on Optitrack's site
To use the Optitrack motion capture system, the cameras must be calibrated. See the [calibration](#starting-motive) section for details. We'll assume for now that someone has calibrated the cameras for you, which will usually be the case. We'll invoke this calibration by choosing to open a previous calibration file. 

The most current calibration file will be tagged with '_current' at the trailing edge of the file. It should reside in the project directory with the rest of the motive project and calibration files. Once you've loaded the calibration, you should be able to navigate to the 3D preview arena and see any rigid bodies that have been marked. You may also see stray readings - refer to the section on  [noise](#noise) for tips on how to mitigate noise in tracking. 

#### Specifying and Managing Rigid Bodies
Motive tracks refelctive markers, but for the most part we'd like to know about the position of ** rigid-bodies**, or a collection of points that define how an object translates and rotates in 3d space. Take the example image of a quadrotor sitting in the center of the capture volume. [todo: insert image of crazyflie w/markers] The orientation of this body only makes sense with respect a second frame of reference. Typically, we care about how the body is oriented with respect to the earth's frame of reference, commonly called the *earth frame*, *world frame*, or *inertial frame* depending on who you ask. With a reference frame, we can reason about how a body is oriented with respect to that reference by examining the sequence of rotations we would take to align the world frame with the body frame. This can be done with a sequence of three rotations, or by a single rotation about some vector. But I digress... 

To create a rigid body in Motive, select three or more markers and then right-click. In the menu, do `Rigid Body -> Create From Selected Markers` You should see that motive has formed a graph between the markers, and has added what it finds to be the center of these points. To keep it simple, you should create the body in the orientation that you would like to be 'zero'. You can reset the orientation or adjust it by doing `View -> Rigis Body Properties`. In the resulting menu, selecting a rigid-body will enable you to see some basic properties, as well as real-time localizaton info. 

Under the tab `Rigid Bodies -> Rigid Bodies -> Advanced`, you should see the `User Data` field. This is the mechanism we will use to identify the body in the stream of data we will grab from Motive. Once you've specified the user data, and have indicated to the packet processor that you'd like to track the body corresponding to that data, you will be able to pick up on Motive's packet stream in pure python.

- [ ] talk about how to do this in other languages

>**Important Note on User Data: **
As of now, it is up to the user to assign values to the user data field. This is done so that we can parse Motive's packets for only relevant data, i.e. the rigid bodies we specify explicitly.


## Streaming Data

To use this system, you will need the following:

- Windows Machine running Motive
- Python script to retrieve Motive's UDP packets, and send over LAN (Run on Windows machine running Motive)[todo: link to appropriate Git Repos]
- A 'client-side' application to retrieve the packets gathered by the Python script.

Todo: we need to sort out UDP multicast directly from Motive. This will allow us to ditch running optirx as its own side process on the Windows box, and to run it 'point of controller'. I.e. instead of:

- [ ] make a diagram of current situation + possible configs
- [ ] describe proposed solution of UDP multicasting direct to OptiRx

You must enable data streaming by doing `View -> Data Streaming`. In the resulting menu, check the box that says `Broadcast Frame Data`. Once this is done, you will be able to start the ZMQ_streaming_server file found here [todo: link to source code for the optirx to zmq packet processing and transmission].

## Reading Data

Now that the data is streaming over the network, we can read it by:

[todo: insert code sample here]

## Multicast
TODO

##Calibration
After initial camera placement or readjustments, it is necessary to calibrate the cameras. The optitrack system works by triangulating the position of reflective markers from a collection of 2D images gathered from the cameras. In order to do this accurately, it is necessary to perform the calibration phase with a wand of known size. In the HSL, we are equipped with the 'Large' wand; it looks like this
[todo:Picture of wand here]

The Calibration procedure is as follows:

1) Start Motive, then do: view -> camera calibration
2) In the perspective view [todo:shown below], click the collection of squares to get to the 2d view
3) In the 2d View, clear all hardware masks by clicking the shield with the negative sign, then add a fresh set by clicking the shield with the posititve sign. Note: Remove all reflective markers from the capture volume during this phase! The hardware masks serve to ignore sources of noise, both intrinsic and extrinisic to the system.
4) Once the hardware masks are in place, we can start wanding. In the camera calibration pane we opened up, do 'start wanding'
5) Now, pick up the large wand and strut your stuff in the capture volume for 3-5 minutes. As you glance over to Motive, you should see colorful streaks populating the array of 2D images the cameras are picking up. If you are not seeing good coverage after a few minutes of wanding you would be well served to repostion the cameras and reattempt wanding. 
6) After you've wanded for several minutes, you should be able to check the calibration results in Motive. Wait until it tells you that you've wanded enough for very high or exceptional results, then hit the calculate button.
7) When calculation is complete, apply the results. 
8) Last, we'll need to reinitialize the coordinate axes. This is done by using the square [todo: add picture of motive square]
9) Now we're almsot done with calibration. As a final, extremely important check for others who will need to use your calibration file, run the motive stream test in PyNatNet to verify that packets are being sent out right on time. You may find it necessary to go to tools -> synchronization and to reinstate a custom synchronization at the given rate, say 120Hz. This should cause the cameras sync input to kick in, and you should observe a time-step of .008 ms corresponding to a frame rate of ~120Hz.

##Noise
todo: write about noise and the steps we can take to mitigate or filter it

The following scripts are available:
- **control:** Runs the control loops
- **set-point:** UI for setting a set-point for the control
- **visualization:** PID visualizations for debugging
