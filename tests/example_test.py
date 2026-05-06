"""Example tests demonstrating fixture usage."""

import pytest


class TestFixtures:
    """Demonstrate how to use the shared fixtures."""

    async def test_mock_ha_client(self, mock_ha_client):
        """Test that mock client returns predictable data."""
        states = await mock_ha_client.get_states()
        assert len(states) == 1
        assert states[0]["entity_id"] == "light.test"
        
        # Verify the mock was called
        mock_ha_client.get_states.assert_called_once()

    async def test_mock_cache(self, mock_cache):
        """Test that cache fixture works with in-memory SQLite."""
        # Cache is synchronous - don't await set/get
        mock_cache.set("light.test", {"state": "on"})
        result = mock_cache.get("light.test")
        
        assert result is not None
        assert result["entity_id"] == "light.test"

    def test_sample_entity(self, sample_entity):
        """Test that sample entity fixture provides valid data."""
        assert sample_entity.entity_id == "light.test"
        assert sample_entity.state == "on"
        assert sample_entity.area_name == "Living Room"

    def test_sample_entities(self, sample_entities):
        """Test that sample entities list is correct."""
        assert len(sample_entities) == 3
        
        # Check domains
        domains = [e.domain for e in sample_entities]
        assert "light" in domains
        assert "sensor" in domains
        assert "switch" in domains

    def test_sample_states(self, sample_states):
        """Test that sample states data is valid."""
        assert len(sample_states) == 2
        assert sample_states[0]["entity_id"] == "light.kitchen"


class TestHAIntegration:
    """Example integration-style tests using fixtures together."""

    async def test_client_and_cache_together(self, mock_ha_client, mock_cache):
        """Test workflow: fetch states from client, cache them."""
        # Fetch states (mocked)
        states = await mock_ha_client.get_states()
        
        # Cache each state - set is synchronous
        for state_item in states:
            entity_id = state_item["entity_id"]
            mock_cache.set(entity_id, state_item)
        
        # Verify cache has the data - get is also synchronous
        cached = mock_cache.get("light.test")
        assert cached is not None
        assert cached["state"] == "on"

    async def test_filter_with_mock_data(self, mock_ha_client):
        """Test filtering logic with mocked HA data."""
        from app.entity_discovery import EntityDiscovery
        
        # Create discovery instance with our mock client
        discovery = EntityDiscovery(mock_ha_client)
        
        # Get states (mocked)
        states = await mock_ha_client.get_states()
        
        # Filter by domain
        filtered = [s for s in states if s["entity_id"].startswith("light")]
        assert len(filtered) == 1
