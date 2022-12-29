import React from "react";
import { useStyles } from "../hooks/useStyles";
import PlayerCard from "./PlayerCard";
import { BLACK, WHITE } from "../constants/Colors";
import ChatCard from "./ChatCard";

// this is a purely organizational component. its only purpose is to pass props
// through divs
function CentralContainer(props) {
  const classes = useStyles();

  return (
    <div className={classes.CentralContainer}>
      <ChatCard {...props} />
      <div className={classes.CentralSubContainer}>
        <PlayerCard {...props} color={BLACK} />
        <PlayerCard {...props} color={WHITE} />
      </div>
    </div>
  );
}

export default CentralContainer;
