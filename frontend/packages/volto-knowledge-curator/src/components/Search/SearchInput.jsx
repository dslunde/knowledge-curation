import React, { useState, useRef, useEffect } from 'react';
import { 
  Input, 
  Button, 
  Dropdown, 
  List,
  Icon,
  Segment,
  Header,
  Label
} from 'semantic-ui-react';

const SearchInput = ({ 
  value, 
  onChange, 
  onSearch, 
  suggestions = [], 
  onInputChange,
  placeholder = "Enter your search...",
  loading = false,
  advanced = false,
  disabled = false
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Handle input change with debouncing for suggestions
  const handleInputChange = (e, { value: inputValue }) => {
    onChange(inputValue);
    
    if (onInputChange && inputValue.length > 1) {
      // Debounce suggestions
      clearTimeout(handleInputChange.debounce);
      handleInputChange.debounce = setTimeout(() => {
        onInputChange(inputValue);
      }, 300);
    }
    
    setShowSuggestions(inputValue.length > 1 && suggestions.length > 0);
    setSelectedSuggestion(-1);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedSuggestion(prev => 
        prev < suggestions.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedSuggestion(prev => prev > 0 ? prev - 1 : prev);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedSuggestion >= 0 && suggestions[selectedSuggestion]) {
        handleSuggestionClick(suggestions[selectedSuggestion]);
      } else {
        handleSearch();
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }
  };

  // Handle search execution
  const handleSearch = () => {
    if (value.trim()) {
      onSearch(value);
      setShowSuggestions(false);
    }
  };

  // Handle suggestion selection
  const handleSuggestionClick = (suggestion) => {
    const suggestionText = typeof suggestion === 'string' ? suggestion : suggestion.text;
    onChange(suggestionText);
    onSearch(suggestionText);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
  };

  // Update suggestions visibility when suggestions change
  useEffect(() => {
    setShowSuggestions(value.length > 1 && suggestions.length > 0);
  }, [suggestions, value]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current && 
        !suggestionsRef.current.contains(event.target) &&
        inputRef.current &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchExamples = [
    "machine learning algorithms",
    "research methodology best practices", 
    "data visualization techniques",
    "python programming concepts",
    "statistical analysis methods"
  ];

  return (
    <div className="search-input-container">
      <div className="search-input-wrapper" ref={inputRef}>
        <Input
          fluid
          size="large"
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          loading={loading}
          action={
            <Button 
              color="blue"
              icon="search"
              content="Search"
              onClick={handleSearch}
              disabled={!value.trim() || loading}
              loading={loading}
            />
          }
          className="search-input"
        />

        {/* Search Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <Segment className="search-suggestions" ref={suggestionsRef}>
            <List selection>
              {suggestions.map((suggestion, index) => {
                const isSelected = index === selectedSuggestion;
                const suggestionText = typeof suggestion === 'string' ? suggestion : suggestion.text;
                const suggestionType = typeof suggestion === 'object' ? suggestion.type : 'suggestion';
                
                return (
                  <List.Item 
                    key={index}
                    active={isSelected}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className={`suggestion-item ${isSelected ? 'selected' : ''}`}
                  >
                    <List.Content>
                      <List.Header>
                        <Icon name={suggestionType === 'content' ? 'file' : 'lightbulb'} />
                        {suggestionText}
                      </List.Header>
                      {suggestion.description && (
                        <List.Description>{suggestion.description}</List.Description>
                      )}
                      {suggestion.count && (
                        <Label size="mini" color="grey">
                          {suggestion.count} results
                        </Label>
                      )}
                    </List.Content>
                  </List.Item>
                );
              })}
            </List>
          </Segment>
        )}
      </div>

      {/* Search Examples for Advanced Mode */}
      {advanced && !value && (
        <Segment basic className="search-examples">
          <Header as="h5" color="grey">
            <Icon name="lightbulb outline" />
            Try searching for:
          </Header>
          <div className="example-tags">
            {searchExamples.map((example, index) => (
              <Label 
                key={index}
                as="a"
                basic
                size="small"
                onClick={() => {
                  onChange(example);
                  onSearch(example);
                }}
                className="search-example"
              >
                {example}
              </Label>
            ))}
          </div>
        </Segment>
      )}

      {/* Search Tips */}
      {advanced && (
        <div className="search-tips">
          <small>
            <Icon name="info circle" color="blue" />
            <strong>Semantic Search Tips:</strong> Use natural language descriptions. 
            Try "explain quantum computing" instead of just "quantum computing".
          </small>
        </div>
      )}
    </div>
  );
};

export default SearchInput; 