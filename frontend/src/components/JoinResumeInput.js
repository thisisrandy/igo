import { TextField, Typography } from "@material-ui/core";
import AutoComplete, {
  createFilterOptions,
} from "@material-ui/lab/Autocomplete";
import React from "react";
import { useStyles } from "../hooks/useStyles";
import { useSelector } from "react-redux";
import { PLAYER_KEY_LENGTH } from "../constants/PlayerKeyInfo";
import { JOIN_RESUME_KEY_FIELD } from "../constants/Ids";
import { getDaysSince } from "../utils";
import { PAST_GAMES } from "../constants/StateKeys";
import { GAME } from "../constants/ReducerKeys";

const filter = createFilterOptions();

function JoinResumeInput({
  setJoinResumeKey,
  canSubmit,
  joinResumeSubmitClick,
  inputRef,
}) {
  const classes = useStyles();
  const { [PAST_GAMES]: pastGames } = useSelector((state) => state[GAME]);

  return (
    <AutoComplete
      id={JOIN_RESUME_KEY_FIELD}
      className={classes.JoinResumeInput}
      autoComplete
      selectOnFocus
      clearOnBlur
      handleHomeEndKeys
      freeSolo
      onKeyPress={(e) => {
        if (e.key === "Enter" && canSubmit) {
          joinResumeSubmitClick();
        }
      }}
      onChange={(_, newValue) => {
        if (typeof newValue === "string") {
          // normal typing (auto-complete ignored)
          setJoinResumeKey(newValue.trim());
        } else if (newValue && newValue.inputValue) {
          // a new value was typed and then selected from the dropdown menu
          setJoinResumeKey(newValue.inputValue.trim());
        } else if (newValue != null) {
          // an existing value was selected from the dropdown
          setJoinResumeKey(newValue.key.trim());
        }
      }}
      filterOptions={(options, params) => {
        const filtered = filter(options, params);

        // Suggest the creation of a new value
        if (params.inputValue !== "") {
          filtered.push({
            inputValue: params.inputValue,
            key: `${params.inputValue}`,
            lastPlayed: "N/A",
          });
        }

        return filtered;
      }}
      options={Object.entries(pastGames)
        .map(([key, lastPlayed]) => ({ key, lastPlayed }))
        .sort((a, b) =>
          // sort desc
          a.lastPlayed < b.lastPlayed ? 1 : a.lastPlayed > b.lastPlayed ? -1 : 0
        )}
      groupBy={(option) => {
        if (
          typeof option === "string" ||
          typeof option.lastPlayed !== "number"
        ) {
          return "(not yet played)";
        }

        const daysSince = getDaysSince(option.lastPlayed);
        if (daysSince === 0) {
          return "Today";
        } else if (daysSince === 1) {
          return "Yesterday";
        } else if (daysSince <= 7) {
          return "This week";
        } else if (daysSince <= 14) {
          return "Last week";
        } else {
          return "Older";
        }
      }}
      getOptionLabel={(option) => {
        if (typeof option === "string") {
          // value selected with enter directly from the input
          return option;
        }
        if (option.inputValue) {
          // a new value typed and then selected from the dropdown menu
          return option.inputValue;
        }
        // extant option from the menu
        return option.key;
      }}
      renderOption={(option) => {
        const date = new Date(option.lastPlayed);

        return (
          <div className={classes.JoinResumeDropdownItemContainer}>
            <Typography style={{ marginRight: 5 }}>{option.key}</Typography>
            {!isNaN(date) && (
              <Typography variant="caption">{`Last viewed: ${date.toLocaleString()}`}</Typography>
            )}
          </div>
        );
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          autoFocus
          label="Player key"
          inputProps={{
            ...params.inputProps,
            ...{
              maxLength: PLAYER_KEY_LENGTH,
              spellCheck: false,
            },
          }}
          inputRef={inputRef}
        />
      )}
    />
  );
}

export default JoinResumeInput;
