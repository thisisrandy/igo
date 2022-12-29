import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  Zoom,
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Tooltip,
  Input,
} from "@material-ui/core";
import React, { useRef, useState } from "react";
import { useStyles } from "../hooks/useStyles";
import { useDispatch, useSelector } from "react-redux";
import { send } from "@giantmachines/redux-websocket";
import { NEW_GAME } from "../constants/OutgoingMessageTypes";
import { TYPE } from "../constants/OutgoingMessageKeys";
import { CONNECTED } from "../constants/StateKeys";
import { DraggableDialogTitle, DraggablePaper } from "./DraggablePaper";
import { COMPUTER, HUMAN } from "../constants/OpponentTypes";
import { VS, COLOR, SIZE, KOMI } from "../constants/OutgoingMessageKeys";
import { BLACK, WHITE } from "../constants/Colors";
import { capitalizeFirstLetter } from "../utils";
import { DEFAULT_BOARD_SIZE, DEFAULT_KOMI } from "../constants/Defaults";
import {
  KOMI_SELECT,
  VS_SELECT,
  COLOR_SELECT,
  BOARD_SIZE_SELECT,
} from "../constants/Ids";
import { GAME } from "../constants/ReducerKeys";

function NewGameDialog({ newGameDialogOpen, setNewGameDialogOpen }) {
  const classes = useStyles();
  const { [CONNECTED]: connected } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();

  const [vs, setVs] = useState(HUMAN);
  const handleVsChange = (e) => {
    setVs(e.target.value);
  };

  const [color, setColor] = useState(BLACK);
  const handleColorChange = (e) => {
    setColor(e.target.value);
  };

  const [size, setSize] = useState(DEFAULT_BOARD_SIZE);
  const handleSizeChange = (e) => {
    setSize(e.target.value);
  };

  const [komi, setKomi] = useState(DEFAULT_KOMI);
  const [komiValid, setKomiValid] = useState(true);
  const handleKomiChange = (e) => {
    const val = e.target.value;
    const asNum = Number(val);
    const fractional = asNum % 1;
    if (
      val.length &&
      !Number.isNaN(asNum) &&
      asNum >= 0 &&
      asNum < 101 &&
      (fractional === 0 || fractional === 0.5)
    ) {
      setKomiValid(true);
      setKomi(asNum);
    } else {
      setKomiValid(false);
    }
  };

  const dialogClose = () => {
    setNewGameDialogOpen(false);
    if (!komiValid) {
      setKomi(DEFAULT_KOMI);
      setKomiValid(true);
    }
  };

  const submit = (e) => {
    setNewGameDialogOpen(false);
    dispatch(
      send({
        [TYPE]: NEW_GAME,
        [VS]: vs,
        [COLOR]: color,
        [SIZE]: size,
        [KOMI]: komi,
      })
    );
  };

  const canSubmit = connected && komiValid;

  const getRadio = () => <Radio color="primary" />;

  const komiInputRef = useRef();
  const onStart = () => {
    komiInputRef.current.blur();
  };

  return (
    <Dialog
      open={newGameDialogOpen}
      onClose={dialogClose}
      PaperComponent={DraggablePaper}
      PaperProps={{ onStart }}
      TransitionComponent={Zoom}
    >
      <DraggableDialogTitle>New Game</DraggableDialogTitle>
      <DialogContent className={classes.DialogContent}>
        <div className={classes.FormContainer}>
          <FormControl>
            <FormLabel component="legend" htmlFor={VS_SELECT}>
              VS.
            </FormLabel>
            <RadioGroup id={VS_SELECT} row onChange={handleVsChange} value={vs}>
              <FormControlLabel
                value={HUMAN}
                control={getRadio()}
                label={HUMAN}
              />
              <Tooltip
                title={
                  "Note that the computer player only plays randomly at the moment." +
                  " Check back later for more"
                }
              >
                <FormControlLabel
                  value={COMPUTER}
                  control={getRadio()}
                  label={COMPUTER}
                />
              </Tooltip>
            </RadioGroup>
          </FormControl>
          <FormControl>
            <FormLabel component="legend" htmlFor={COLOR_SELECT}>
              Your Color
            </FormLabel>
            <RadioGroup
              id={COLOR_SELECT}
              row
              onChange={handleColorChange}
              value={color}
            >
              <FormControlLabel
                value={BLACK}
                control={getRadio()}
                label={BLACK}
              />
              <FormControlLabel
                value={WHITE}
                control={getRadio()}
                label={WHITE}
              />
            </RadioGroup>
          </FormControl>
          <FormControl>
            <FormLabel component="legend" htmlFor={BOARD_SIZE_SELECT}>
              Board Size
            </FormLabel>
            <div className={classes.BoardSizeSelectContainer}>
              <Select
                id={BOARD_SIZE_SELECT}
                className={classes.BoardSizeSelect}
                value={size}
                onChange={handleSizeChange}
              >
                <MenuItem value={9}>9x9</MenuItem>
                <MenuItem value={13}>13x13</MenuItem>
                <MenuItem value={19}>19x19</MenuItem>
              </Select>
            </div>
          </FormControl>
          <FormControl>
            <FormLabel component="legend" htmlFor={KOMI_SELECT}>
              {capitalizeFirstLetter(KOMI)}
            </FormLabel>
            <div className={classes.KomiTextContainer}>
              <Input
                id={KOMI_SELECT}
                name={KOMI}
                className={classes.KomiTextField}
                type="number"
                inputProps={{
                  min: 0,
                  max: 100.5,
                  step: 0.5,
                }}
                defaultValue={komi}
                error={!komiValid}
                onChange={handleKomiChange}
                onKeyPress={(e) => {
                  if (e.key === "Enter" && canSubmit) {
                    submit();
                  }
                }}
                inputRef={komiInputRef}
              />
            </div>
          </FormControl>
        </div>
      </DialogContent>
      <DialogActions
        disableSpacing={true}
        className={classes.DialogButtonContainer}
      >
        <Button
          className={classes.Button}
          variant="contained"
          onClick={submit}
          disabled={!canSubmit}
        >
          Submit
        </Button>
        <Button
          className={classes.Button}
          variant="contained"
          onClick={dialogClose}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default NewGameDialog;
