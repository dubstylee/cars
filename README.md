# cars
implement 4-lane autonomous car intersection

![grid](./gui.png?raw=true "Intersection Grid")

<b>Image summary:</b>
<ul>
  <li>Vehicle 1 in lane 1 is going straight.</li>
  <li>Vehicle 3 in lane 3 is turning right.</li>
  <li>The property section at the bottom displays the status of the four properties. These properties ensure that the cz squares are locked before a vehicle moves into them, and that the locks are released afterward.</li>
  <li>Below the intersection graphic, the "MOVE 1 cz3" is the action taken in the last step.</li>
  <li>The right-hand section displays the status of the asserts associated with the four cz squares. These asserts are similar to the properties, but they are implemented using fluents which are displayed using the Edison.</li>
</ul>

<b>CAR</b>
<p>Each car knows which lane is is assigned to, as well as the different moves it can take. For example, car 1 in lane 1 will have the following actions: <b>{"straight": [cz1,cz3], "turn_right": [cz1]}</b>. The list of czs represent the CZ squares which the car must get permission to access before proceeding.</p>
<p>Our demo can run with 4 or 8 cars. There are no convoys, but the method of token passing allows for some level of concurrency.</p>

<b>TOKEN</b>
<p>The cars use a form of token-passing to give each lane the right-of-way. The order for a four-car system is 1-3-2-4. A car will pass the token as soon as it has acquired all the necessary locks it needs in order to move. The locks are released once the car has moved out of a locked CZ square.</p>
