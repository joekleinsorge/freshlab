package main

import (
	"fmt"
	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/list"
	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"golang.org/x/crypto/ssh"
)

var hosts = []string{"metal1", "metal2", "metal3"}

var enterKey = key.NewBinding(key.WithKeys("enter"))

type hostItem string

func (item hostItem) FilterValue() string {
	return string(item)
}

type model struct {
	spinner       spinner.Model
	list          list.Model
	err           error
	selected      map[int]struct{}
	sshConfig     *ssh.ClientConfig
	usernameInput textinput.Model
	passwordInput textinput.Model
}

func initialModel() model {
	items := make([]list.Item, len(hosts))
	for i := range hosts {
		items[i] = hostItem(hosts[i])
	}

	s := spinner.NewModel()
	s.Spinner = spinner.Dot

	l := list.NewModel(items, list.NewDefaultDelegate(), 0, 0)

	usernameInput := textinput.NewModel()
	usernameInput.Placeholder = "Username"
	usernameInput.Focus()

	passwordInput := textinput.NewModel()
	passwordInput.Placeholder = "Password"
	passwordInput.EchoMode = textinput.EchoPassword
	passwordInput.EchoCharacter = '*'

	return model{
		spinner:       s,
		list:          l,
		sshConfig:     &ssh.ClientConfig{},
		selected:      make(map[int]struct{}),
		usernameInput: usernameInput,
		passwordInput: passwordInput,
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) View() string {
	return lipgloss.JoinVertical(lipgloss.Left,
		m.list.View(),
		m.spinner.View(),
		m.usernameInput.View(),
		m.passwordInput.View(),
	)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch {
		case key.Matches(msg, enterKey):
			if m.usernameInput.Focused() {
				m.sshConfig.User = m.usernameInput.Value()
				return m, textinput.Blink
			} else if m.passwordInput.Focused() {
				m.sshConfig.Auth = append(m.sshConfig.Auth, ssh.Password(m.passwordInput.Value()))
				return m, textinput.Blink
			}
			// Handle SSH connection attempt logic here
			// Use m.sshConfig and m.list.Selected() to determine the selected host
			// Update m.spinner and m.err accordingly
		}
	}

	return m, nil
}

func main() {
	p := tea.NewProgram(initialModel())
	if err := p.Start(); err != nil {
		fmt.Println("Error running program:", err)
	}
}
