#!/usr/bin/env node

// Debug script to test regex pattern matching
const dirName = "The_Weeknd_-_Blinding_Lights_Official_Video_b32060_20250811_201649";

console.log('🔍 Testing regex patterns for:', dirName);
console.log('=====================================');

// Test different patterns
const patterns = [
  `${dirName}_melody.txt`,
  `${dirName.replace(/_.*$/, '')}_melody.txt`,
  `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '')}_melody.txt`,
  `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '').replace(/_.*$/, '')}_melody.txt`
];

patterns.forEach((pattern, index) => {
  console.log(`Pattern ${index + 1}: ${pattern}`);
});

console.log('\n🎯 What we need: The_Weeknd_-_Blinding_Lights_O_melody.txt');

// Test the actual file name
const actualFile = "The_Weeknd_-_Blinding_Lights_O_melody.txt";
console.log(`\n📁 Actual file: ${actualFile}`);

// Try to find a pattern that matches
const testPatterns = [
  dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '').replace(/_.*$/, ''),
  dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, ''),
  dirName.replace(/_.*$/, ''),
  dirName.split('_')[0] + '_' + dirName.split('_')[1] + '_' + dirName.split('_')[2]
];

testPatterns.forEach((pattern, index) => {
  const testFile = `${pattern}_melody.txt`;
  console.log(`Test ${index + 1}: ${testFile} ${testFile === actualFile ? '✅ MATCH!' : '❌'}`);
});
