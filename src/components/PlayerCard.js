import { Paper, Typography } from "@material-ui/core";
import React from "react";
import { useStyles } from "../hooks/useStyles";
import black from "../images/black.png";
import white from "../images/white.png";

function PlayerCard({ color }) {
  const classes = useStyles();

  return (
    <Paper className={classes.PlayerCardContainer}>
      <Paper className={classes.PlayerCardSubContainer}>
        <img
          src={color === "white" ? white : black}
          alt="player piece display"
          className={classes.PlayerStoneImage}
        />
      </Paper>
      <Paper className={classes.PlayerCardSubContainer}>
        <Typography>Prisoners: 0</Typography>
        <Typography>Territory: -</Typography>
        <Typography>Total Score: -</Typography>
      </Paper>
    </Paper>
  );
}

export default PlayerCard;
