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
