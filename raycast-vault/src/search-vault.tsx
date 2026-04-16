import { List, ActionPanel, Action, showToast, Toast } from "@raycast/api";
import { useState, useEffect } from "react";
import fetch from "node-fetch";

export default function Command() {
  const [searchText, setSearchText] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function search() {
      if (!searchText) {
        setResults([]);
        return;
      }
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8001/api/search?q=${encodeURIComponent(searchText)}`);
        const data: any = await response.json();
        setResults(data.results || []);
      } catch (err) {
        showToast({ style: Toast.Style.Failure, title: "NeuralVault Offline", message: "Ensure api.py is running on port 8001" });
      } finally {
        setIsLoading(false);
      }
    }
    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [searchText]);

  return (
    <List 
        onSearchTextChange={setSearchText} 
        isLoading={isLoading} 
        searchBarPlaceholder="Search your sub-conscious..."
        throttle
    >
      {results.map((r: any) => (
        <List.Item
          key={r.id}
          title={r.text}
          subtitle={`Score: ${(r.score * 100).toFixed(1)}%`}
          accessories={[{ text: r.metadata?.source || "unknown" }]}
          actions={
            <ActionPanel>
              <Action.CopyToClipboard title="Copy Text" content={r.text} />
              <Action.Paste title="Paste as Sinapse" content={r.text} />
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
