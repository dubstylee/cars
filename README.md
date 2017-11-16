# cars
implement 4-lane autonomous car intersection

![grid](./grid.png?raw=true "Intersection Grid")

<b>Image summary:</b>
<ul>
  <li>Lanes are numbered 1-4.</li>
  <li>Vehicles are named A-H</li>
  <li>Conflict Zone (CZ) is labeled with Cartesian coordinates (x,y)</li>
</ul>

<b>CAR</b>
<p>Each car will know which lane is is assigned to, as well as the different moves it can take. For example, car A in lane 1 will have the following actions: <b>{"straight": [(1,2),(1,4)], "turn_right": [(1,2)]}</b>. The list of coordinates following the action represent the CZ squares which the car must get permission to access before proceeding.</p>
<p>Initially, we will begin with only four cars: A, C, E, and G. Eventually, we would like to implement a 2-car convoy algorithm, so that when car A has permission to proceed, car A will notify car B that it is ok to follow. This can be more complicated if B is going straight while A is turning right. Maybe convoy will need to make sure that the trailing vehicles are making the same movement.</p>

<b>TOKEN</b>
<p>The cars will (maybe?) use a form of token-passing to give each lane the right-of-way. Alternatively, cars may just use some form of broadcasting when they would like to move, and implement a form of the Ricart-Agrawala algorithm to determine permission.</p>
